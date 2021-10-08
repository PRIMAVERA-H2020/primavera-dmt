#!/usr/bin/env python
"""
validate_data_submission.py

This script is run by users to validate submitted data files and to create a
data submission in the Data Management Tool.
"""
from __future__ import unicode_literals, division, absolute_import
import argparse
import datetime
import itertools
import json
import logging.config
from multiprocessing import Process, Manager
from multiprocessing.pool import ThreadPool
from netCDF4 import Dataset
import os
import re
import shutil
import subprocess
import sys
import time
import warnings

try:
    import dask
except ImportError:
    pass
import iris

from primavera_val import (identify_filename_metadata, validate_file_contents,
                           identify_contents_metadata,
                           validate_cell_measures_contents,
                           identify_cell_measures_metadata, load_cube,
                           FileValidationError)

import django
django.setup()

from django.contrib.auth.models import User

from pdata_app.models import (Project, ClimateModel, Experiment, DataSubmission,
    DataFile, VariableRequest, DataRequest, Checksum, Settings, Institute,
    ActivityId, EmailQueue)
from pdata_app.utils.dbapi import get_or_create, match_one
from pdata_app.utils.common import adler32, list_files, pdt2num
from vocabs.vocabs import STATUS_VALUES, CHECKSUM_TYPES

# Ignore warnings displayed when loading data
warnings.filterwarnings("ignore")

__version__ = '0.1.0b'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

CONTACT_PERSON_USER_ID = 'jseddon'

# The maximum size (in bytes) of file to read into memory for an HDF
# data integrity check
# 1073741824 = 1 GiB
MAX_DATA_INTEGRITY_SIZE = 1073741824

# Don't run PrePARE on the following var/table combinations as they've
# been removed from the CMIP6 data request, but are still needed for
# PRIMAVERA
# Additionally, don't run PrePARE on any of the PRIMAVERA only tables
SKIP_PREPARE_VARS = ['psl_E3hrPt', 'ua850_E3hrPt', 'va850_E3hrPt',
                     'mrlsl_Emon', 'mrlsl_Lmon', 'sialb_SImon',
                     'tso_3hr',
                     'Prim1hr', 'Prim3hr', 'Prim3hrPt', 'Prim6hr',
                     'Prim6hrPt', 'PrimO6hr', 'PrimOday', 'PrimOmon',
                     'PrimSIday', 'Primday', 'PrimdayPt', 'Primmon',
                     'PrimmonZ',
]


class SubmissionError(Exception):
    """
    An exception to indicate that there has been an error that means that
    the data submission cannot continue.
    """
    pass


def identify_and_validate(filenames, project, num_processes, file_format):
    """
    Loop through a list of file names, identify each file's metadata and then
    validate it. The looping is done in parallel using the multiprocessing
    library module.

    clt_Amon_HadGEM2-ES_historical_r1i1p1_185912-188411.nc

    :param list filenames: The files to process
    :param str project: The name of the project
    :param int num_processes: The number of parallel processes to use
    :param str file_format: The CMOR version of the netCDF files, one out of-
        CMIP5 or CMIP6
    :returns: A list containing the metadata dictionary generated for each file
    :rtype: multiprocessing.Manager.list
    """
    jobs = []
    manager = Manager()
    params = manager.Queue()
    result_list = manager.list()
    error_event = manager.Event()
    if num_processes != 1:
        for i in range(num_processes):
            p = Process(target=identify_and_validate_file, args=(params,
                result_list, error_event))
            jobs.append(p)
            p.start()

    func_input_pair = list(zip(filenames,
                          (project,) * len(filenames),
                          (file_format,) * len(filenames)))
    blank_pair = (None, None, None)

    iters = itertools.chain(func_input_pair, (blank_pair,) * num_processes)
    for item in iters:
        params.put(item)

    if num_processes == 1:
        identify_and_validate_file(params, result_list, error_event)
    else:
        for j in jobs:
            j.join()

    if error_event.is_set():
        raise SubmissionError()

    return result_list


def identify_and_validate_file(params, output, error_event):
    """
    Identify `filename`'s metadata and then validate the file. The function
    continues getting items to process from the parameter queue until a None
    is received.

    :param multiprocessing.Manager.Queue params: A queue, with each item being a
        tuple of the filename to load, the name of the project and the netCDF
        file CMOR version
    :param multiprocessing.Manager.list output: A list containing the output
        metadata dictionaries for each file
    :param multiprocessing.Manager.Event error_event: If set then a catastrophic
        error has occurred in another process and processing should end
    """
    while True:
        # close existing connections so that a fresh connection is made
        django.db.connections.close_all()

        if error_event.is_set():
            return

        filename, project, file_format = params.get()

        if filename is None:
            return

        try:
            _identify_and_validate_file(filename, project, file_format,output,
                                        error_event)
        except django.db.utils.OperationalError:
            # Wait and then re-run once in case of temporary database
            # high load
            logger.warning('django.db.utils.OperationalError waiting for one '
                           'minute and then retrying.')
            time.sleep(60)
            try:
                _identify_and_validate_file(filename, project, file_format,
                                            output, error_event)
            except django.db.utils.OperationalError:
                logger.error('django.db.utils.OperationalError for a second '
                             'time. Exiting.')
                error_event.set()
                raise


def _identify_and_validate_file(filename, project, file_format, output,
                                error_event):
    """
    Do the validation of a file.

    :param str filename: The name of the file
    :param str project: The name of the project
    :param str file_format: The format of the file (CMIP5 or CMIP6)
    :param multiprocessing.Manager.list output: A list containing the output
        metadata dictionaries for each file
    :param multiprocessing.Manager.Event error_event: If set then a catastrophic
        error has occurred in another process and processing should end
    """
    try:
        basename = os.path.basename(filename)
        if DataFile.objects.filter(name=basename).count() > 0:
            msg = 'File {} already exists in the database.'.format(basename)
            raise FileValidationError(msg)

        metadata = identify_filename_metadata(filename, file_format)

        if metadata['table'].startswith('Prim'):
            metadata['project'] = 'PRIMAVERA'
        else:
            metadata['project'] = project

        if 'fx' in metadata['table']:
            cf = iris.fileformats.cf.CFReader(filename)
            metadata.update(identify_cell_measures_metadata(cf, filename))
            validate_cell_measures_contents(cf, metadata)
        else:
            cube = load_cube(filename)
            metadata.update(identify_contents_metadata(cube, filename))
            validate_file_contents(cube, metadata)
            _contents_hdf_check(cube, metadata, cmd_args.data_limit)

        verify_fk_relationships(metadata)

        calculate_checksum(metadata)
    except SubmissionError:
        msg = ('A serious file error means the submission cannot continue: '
               '{}'.format(filename))
        logger.error(msg)
        error_event.set()
    except FileValidationError as fve:
        msg = 'File failed validation. {}'.format(fve.__str__())
        logger.warning(msg)
    else:
        output.append(metadata)


def calculate_checksum(metadata):
    checksum_value = adler32(os.path.join(metadata['directory'],
                                          metadata['basename']))
    if checksum_value:
        metadata['checksum_type'] = CHECKSUM_TYPES['ADLER32']
        metadata['checksum_value'] = checksum_value
    else:
        msg = ('Unable to calculate checksum for file: {}'.
               format(metadata['basename']))
        logger.warning(msg)
        metadata['checksum_type'] = None
        metadata['checksum_value'] = None


def verify_fk_relationships(metadata):
    """
    Identify the variable_request and data_request objects corresponding to this file.

    :param dict metadata: Metadata identified for this file.
    :raises SubmissionError: If there are no existing entries in the
        database for `Project`, `ClimateModel` or `Experiment`.
    """
    foreign_key_types = [
        (Project, 'project'),
        (ClimateModel, 'climate_model'),
        (Experiment, 'experiment'),
        (Institute, 'institute'),
        (ActivityId, 'activity_id')]

    # get values for each of the foreign key types
    for object_type, object_str in foreign_key_types:
        result = match_one(object_type, short_name=metadata[object_str])
        if result:
            metadata[object_str] = result
        else:
            msg = ("No {} '{}' found for file: {}. Please create this object "
                "and resubmit.".format(object_str.replace('_', ' '),
                metadata[object_str], metadata['basename']))
            logger.error(msg)
            raise SubmissionError(msg)

    # find the data request
    dreq_match = match_one(
        DataRequest,
        project=metadata['project'],
        institute=metadata['institute'],
        climate_model=metadata['climate_model'],
        experiment=metadata['experiment'],
        variable_request__table_name=metadata['table'],
        variable_request__cmor_name=metadata['var_name'],
        rip_code=metadata['rip_code']
    )
    if dreq_match:
        metadata['data_request'] = dreq_match
        metadata['variable'] = dreq_match.variable_request
    else:
        # if cmor_name doesn't match then it may be a variable where out_name
        # is different to cmor_name so check these
        dreq_matches = DataRequest.objects.filter(
            project=metadata['project'],
            institute=metadata['institute'],
            climate_model=metadata['climate_model'],
            experiment=metadata['experiment'],
            variable_request__table_name=metadata['table'],
            variable_request__var_name=metadata['var_name'],
            rip_code=metadata['rip_code']
        )
        if dreq_matches.count() == 0:
            msg = ('No data request found for file: {}.'.
                   format(metadata['basename']))
            logger.error(msg)
            raise FileValidationError(msg)
        elif dreq_matches.count() == 1:
            metadata['data_request'] = dreq_matches[0]
            metadata['variable'] = dreq_matches[0].variable_request
        else:
            try:
                plev_name = _guess_plev_name(metadata)
            except Exception:
                msg = ('Cannot open file to determine plev name: {}.'.
                       format(metadata['basename']))
                logger.error(msg)
                raise FileValidationError(msg)
            if plev_name:
                plev_matches = dreq_matches.filter(
                    variable_request__dimensions__icontains=plev_name
                )
                if plev_matches.count() == 1:
                    metadata['data_request'] = plev_matches[0]
                    metadata['variable'] = plev_matches[0].variable_request
                elif plev_matches.count() == 0:
                    msg = ('No data requests found with plev {} for file: {}.'.
                           format(plev_name, metadata['basename']))
                    logger.error(msg)
                    raise FileValidationError(msg)
                else:
                    msg = ('Multiple data requests found with plev {} for '
                           'file: {}.'.format(plev_name, metadata['basename']))
                    logger.error(msg)
                    raise FileValidationError(msg)
            else:
                msg = ('Unable to determine plev name: {}.'.
                       format(metadata['basename']))
                logger.error(msg)
                raise FileValidationError(msg)


def update_database_submission(validated_metadata, data_sub, files_online=True,
                               file_version=None):
    """
    Create entries in the database for the files in this submission.

    :param list validated_metadata: A list containing the metadata dictionary
        generated for each file
    :param pdata_app.models.DataSubmission data_sub: The data submission object
        to update.
    :param bool files_online: True if the files are online.
    :returns:
    """
    for data_file in validated_metadata:
        create_database_file_object(data_file, data_sub, files_online,
                                    file_version)

    data_sub.status = STATUS_VALUES['VALIDATED']
    data_sub.save()


def read_json_file(filename):
    """
    Read a JSON file describing the files in this submission.

    :param str filename: The name of the JSON file to read.
    :returns: a list of dictionaries containing the validated metadata
    """
    with open(filename) as fh:
        metadata = json.load(fh, object_hook=_dict_to_object)

    logger.debug('Metadata for {} files read from JSON file {}'.format(
        len(metadata), filename))

    return metadata


def write_json_file(validated_metadata, filename):
    """
    Write a JSON file describing the files in this submission.

    :param list validated_metadata: A list containing the metadata dictionary
        generated for each file
    :param str filename: The name of the JSON file to write the validated data
        to.
    """
    with open(filename, 'w') as fh:
        json.dump(list(validated_metadata), fh, default=_object_to_default,
                  indent=4)

    logger.debug('Metadata written to JSON file {}'.format(filename))


def create_database_file_object(metadata, data_submission, file_online=True,
                                file_version=None):
    """
    Create a database entry for a data file

    :param dict metadata: This file's metadata.
    :param pdata_app.models.DataSubmission data_submission: The parent data
        submission.
    :param bool file_online: True if the file is online.
    :param str file_version: The version string to apply to each file. The 
        string from the incoming directory name or the current date is used
        if a string isn't supplied.
    :returns:
    """
    # get a fresh DB connection after exiting from parallel operation
    django.db.connections.close_all()

    time_units = Settings.get_solo().standard_time_units

    if file_version:
        version_string = file_version
    else:
        # find the version number from the date in the submission directory path
        date_string = re.search(r'(?<=/incoming/)(\d{8})',
                                metadata['directory'])
        if date_string:
            date_string = date_string.group(0)
            version_string = 'v' + date_string
        else:
            today = datetime.datetime.utcnow()
            version_string = today.strftime('v%Y%m%d')

    # if the file isn't online (e.g. loaded from JSON) then directory is blank
    directory = metadata['directory'] if file_online else None

    # create a data file. If the file already exists in the database with
    # identical metadata then nothing happens. If the file exists but with
    # slightly different metadata then django.db.utils.IntegrityError is
    # raised
    try:
        data_file = DataFile.objects.create(
            name=metadata['basename'],
            incoming_name=metadata['basename'],
            incoming_directory=metadata['directory'],
            directory=directory, size=metadata['filesize'],
            project=metadata['project'],
            institute=metadata['institute'],
            climate_model=metadata['climate_model'],
            activity_id=metadata['activity_id'],
            experiment=metadata['experiment'],
            variable_request=metadata['variable'],
            data_request=metadata['data_request'],
            frequency=metadata['frequency'], rip_code=metadata['rip_code'],
            start_time=pdt2num(metadata['start_date'], time_units,
                               metadata['calendar']) if metadata['start_date']
                                            else None,
            end_time=pdt2num(metadata['end_date'], time_units,
                             metadata['calendar'], start_of_period=False) if
                             metadata['start_date'] else None,
            time_units=time_units, calendar=metadata['calendar'],
            version=version_string,
            data_submission=data_submission, online=file_online,
            grid=metadata.get('grid'),
            tape_url = metadata.get('tape_url')
        )
    except django.db.utils.IntegrityError as exc:
        msg = ('Unable to submit file {}: {}'.format(metadata['basename'],
                                                     exc.__str__()))
        logger.error(msg)
        raise SubmissionError(msg)

    if metadata['checksum_value']:
        checksum = get_or_create(Checksum, data_file=data_file,
                                 checksum_value=metadata['checksum_value'],
                                 checksum_type=metadata['checksum_type'])


def move_rejected_files(submission_dir):
    """
    Move the entire submission to a rejected directory two levels up from the
    submission directory.

    :param str submission_dir:
    :returns: The path to the submission after the function has run.
    """
    rejected_dir = os.path.normpath(os.path.join(submission_dir, '..',
                                                 '..', 'rejected'))
    try:
        if not os.path.exists(rejected_dir):
            os.mkdir(rejected_dir)

        shutil.move(submission_dir, rejected_dir)
    except (IOError, OSError):
        msg = ("Unable to move the directory. Leaving it in it's current "
               "location")
        logger.error(msg)
        return submission_dir

    submission_rejected_dir = os.path.join(rejected_dir,
        os.path.basename(os.path.abspath(submission_dir)))

    msg = 'Data submission moved to {}'.format(submission_rejected_dir)
    logger.error(msg)

    return submission_rejected_dir


def send_user_rejection_email(data_sub):
    """
    Send an email to the submission's creator warning them of validation
    failure.

    :param pdata_app.models.DataSubmission data_sub:
    """
    val_tool_url = ('http://proj.badc.rl.ac.uk/primavera-private/wiki/JASMIN/'
                    'HowTo#SoftwarepackagesinstalledonthePRIMAVERAworkspace')

    contact_user_id = Settings.get_solo().contact_user_id
    contact_user = User.objects.get(username=contact_user_id)
    contact_string = '{} {} ({})'.format(contact_user.first_name,
                                         contact_user.last_name,
                                         contact_user.email)

    msg = (
        'Dear {first_name} {surname},\n'
        '\n'
        'Your data submission in {incoming_dir} has failed validation and '
        'has been moved to {rejected_dir}.\n'
        '\n'
        'Please run the validation tool ({val_tool_url}) to check why this '
        'submission failed validation. Once the data is passing validation '
        'then please resubmit the corrected data.\n'
        '\n'
        'Please contact {contact_person} if you '
        'have any questions.\n'
        '\n'
        'Thanks,\n'
        '\n'
        '{friendly_name}'.format(
        first_name=data_sub.user.first_name, surname=data_sub.user.last_name,
        incoming_dir=data_sub.incoming_directory,
        rejected_dir=data_sub.directory, val_tool_url=val_tool_url,
        contact_person=contact_string,
        friendly_name=contact_user.first_name
    ))

    _email = EmailQueue.objects.create(
        recipient=data_sub.user,
        subject='[PRIMAVERA_DMT] Data submission failed validation',
        message=msg)


def send_admin_rejection_email(data_sub):
    """
    Send the admin user an email warning them that a submission failed due to
    a server problem (missing data request, etc).

    :param pdata_app.models.DataSubmission data_sub:
    """
    admin_user_id = Settings.get_solo().contact_user_id
    admin_user = User.objects.get(username=admin_user_id)

    msg = (
        'Data submission {} from incoming directory {} failed validation due '
        'to a SubmissionError being raised. Please run the validation script '
        'manually on this submission and correct the error.\n'
        '\n'
        'Thanks,\n'
        '\n'
        '{}'.format(data_sub.id, data_sub.incoming_directory,
                    admin_user.first_name)
    )

    _email = EmailQueue.objects.create(
        recipient=admin_user,
        subject=('[PRIMAVERA_DMT] Submission {} failed validation'.
                 format(data_sub.id)),
        message=msg
    )


def set_status_rejected(data_sub, rejected_dir):
    """
    Set the data submission's status to be rejected and update the path to
    point to where the data now lives.

    :param pdata_app.models.DataSubmission data_sub: The data submission object.
    :param str rejected_dir: The name of the directory that the rejected files
        have been moved to.
    """
    data_sub.status = STATUS_VALUES['REJECTED']
    data_sub.directory = rejected_dir
    data_sub.save()


def add_tape_url(metadata, tape_base_url, submission_dir):
    """
    Add to each file's metadata its URL in the tape system. The URL is
    calculated by finding the file's path relative to the submission directory
    and appending this to the base URL.

    :param list metadata: a list the dictionary object corresponding to
        each file
    :param str tape_base_url: the top level url of the data in the tape system
    :param str submission_dir: the top-level directory of the submission
    """
    for data_file in metadata:
        rel_dir = os.path.relpath(data_file['directory'], submission_dir)
        data_file['tape_url'] = tape_base_url + '/' + rel_dir


def run_prepare(file_paths, num_processes):
    """
    Run PrePARE on each file in the submission. Any failures are reported
    as an error with the logging and an exception is raised at the end of
    processing if one or more files has failed.

    :param list file_paths: The paths of the files in the submission's
        directory.
    :param int num_processes: The number of processes to use in parallel.
    :raises SubmissionError: at the end of checking if one or more files has
    failed PrePARE's checks.
    """
    logger.debug('Starting PrePARE on {} files'.format(len(file_paths)))
    jobs = []
    manager = Manager()
    params = manager.Queue()
    file_failed = manager.Event()
    if num_processes != 1:
        for i in range(num_processes):
            p = Process(target=_run_prepare, args=(params, file_failed))
            jobs.append(p)
            p.start()

    for item in itertools.chain(file_paths, (None,) * num_processes):
        params.put(item)

    if num_processes == 1:
        _run_prepare(params, file_failed)
    else:
        for j in jobs:
            j.join()

    if file_failed.is_set():
        logger.error('Not all files passed PrePARE')
        raise SubmissionError()

    logger.debug('All files successfully checked by PrePARE')


def _contents_hdf_check(cube, metadata, max_size=MAX_DATA_INTEGRITY_SIZE):
    """
    Check that the entire data of the file can be read into memory without
    any errors. Corrupt files typically generate an HDF error. Files larger
    than `max_size` are not read and a warning is displayed. Most files are
    under this limit, but those over are excessively slow to validate.

    :param iris.cube.Cube cube: The cube to check
    :param dict metadata: Metadata obtained from the file
    :param int max_size: Files larger than this (in bytes) are not checked
    :returns: True if file read ok.
    :raises FileValidationError: If there was any problem reading the data.
    """
    if os.path.getsize(os.path.join(metadata['directory'],
                                    metadata['basename'])) > max_size:
        logger.warning('File {} is larger than {} bytes. File contents '
                       'reading check not run.'.format(metadata['basename'],
                                                       max_size))
        return True

    try:
        _data = cube.data
    except Exception:
        msg = 'Unable to read data from file {}.'.format(metadata['basename'])
        raise FileValidationError(msg)
    else:
        return True


def _run_prepare(params, file_failed):
    """
    Check a single file with PrePARE. This function is called in parallel by
    multiprocessing.

    :param multiprocessing.Manager.Queue params: A queue, with each item being
        the full path of a file in the submission to check.
    :param multiprocessing.Manager.Event file_failed: If set then one or more
        files has failed validation.
    """
    while True:
        file_path = params.get()

        if file_path is None:
            return

        skip_this_var = False
        for skip_var in SKIP_PREPARE_VARS:
            if skip_var in file_path:
                logger.debug('Skipping running PrePARE on {}'.
                             format(file_path))
                skip_this_var = True
                break
        if skip_this_var:
            continue

        prepare_script = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'run_prepare.sh'
        )

        prep_res = subprocess.run([prepare_script, file_path],
                                  stdout=subprocess.PIPE)

        if prep_res.returncode:
            logger.error('File {} failed PrePARE\n{}'.
                         format(file_path, prep_res.stdout.decode('utf-8')))
            file_failed.set()


def _get_submission_object(submission_dir):
    """
    :param str submission_dir: The path of the submission's top level
    directory.
    :returns: The object corresponding to the submission.
    :rtype: pdata_app.models.DataSubmission
    """
    try:
        data_sub = DataSubmission.objects.get(incoming_directory=submission_dir)
    except django.core.exceptions.MultipleObjectsReturned:
        msg = 'Multiple DataSubmissions found for directory: {}'.format(
            submission_dir)
        logger.error(msg)
        raise SubmissionError(msg)
    except django.core.exceptions.ObjectDoesNotExist:
        msg = ('No DataSubmissions have been found in the database for '
               'directory: {}. Please create a submission through the web '
               'interface.'.format(submission_dir))
        logger.error(msg)
        raise SubmissionError(msg)

    return data_sub


def _guess_plev_name(metadata):
    """
    Guess the name of the plev in the data request dimensions.
    
    :param dict metadata: The file's metadata dictionary. 
    :returns: The name of the pressure levels from the data request or none
        if it can't be guessed.
    :rtype: str
    """
    rootgrp = Dataset(os.path.join(metadata['directory'],
                                   metadata['basename']))
    level_name = None

    if 'plev' in rootgrp.dimensions:
        level_name = 'plev'
    elif 'lev' in rootgrp.dimensions:
        level_name = 'lev'

    if level_name:
        num_plevs = len(rootgrp.dimensions[level_name])
        if num_plevs == 4:
            plev_val = 'plev4'
        elif num_plevs == 7:
            plev_val = 'plev7h'
        elif num_plevs == 27:
            plev_val = 'plev27'
        else:
            plev_val = None
    else:
        plev_val = None

    rootgrp.close()
    return plev_val


def _object_to_default(obj):
    """
    Convert known objects to a form that can be serialized by JSON
    """
    if isinstance(obj, iris.time.PartialDateTime):
        obj_dict = {'__class__': obj.__class__.__name__,
                    '__module__': obj.__module__}
        kwargs = {}
        for k, v in re.findall(r'(\w+)=(\d+)', repr(obj)):
            kwargs[k] = int(v)
        obj_dict['__kwargs__'] = kwargs

        return obj_dict
    elif isinstance(obj, (ActivityId, ClimateModel, Experiment, Institute,
                          Project)):
        obj_dict = {'__class__': obj.__class__.__name__,
                    '__module__': obj.__module__}
        obj_dict['__kwargs__'] = {'short_name': obj.short_name}
        return obj_dict
    elif isinstance(obj, VariableRequest):
        obj_dict = {'__class__': obj.__class__.__name__,
                    '__module__': obj.__module__}
        obj_dict['__kwargs__'] = {'table_name': obj.table_name,
                                  'cmor_name': obj.cmor_name}
        return obj_dict
    elif isinstance(obj, DataRequest):
        obj_dict = {'__class__': obj.__class__.__name__,
                    '__module__': obj.__module__}
        obj_dict['__kwargs__'] = {
            'variable_request__table_name': obj.variable_request.table_name,
            'variable_request__cmor_name': obj.variable_request.cmor_name,
            'institute__short_name': obj.institute.short_name,
            'climate_model__short_name': obj.climate_model.short_name,
            'experiment__short_name': obj.experiment.short_name,
            'rip_code': obj.rip_code
        }
        return obj_dict


def _dict_to_object(dict_):
    """
    Convert a dictionary to an object
    """
    if '__class__' in dict_:
        module = __import__(dict_['__module__'], fromlist=[dict_['__class__']])
        klass = getattr(module, dict_['__class__'])
        if dict_['__class__'] == 'PartialDateTime':
            inst = klass(**dict_['__kwargs__'])
        elif dict_['__class__'] in ('ActivityId', 'ClimateModel',
                                    'Experiment', 'Institute', 'Project',
                                    'VariableRequest', 'DataRequest'):
            inst = match_one(klass, **dict_['__kwargs__'])
        else:
            msg = ('Cannot load from JSON files class {}'.
                   format(dict_['__class__']))
            raise NotImplementedError(msg)
    else:
        inst = dict_
    return inst


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Validate and create a '
        'PRIMAVERA data submission')
    parser.add_argument('directory', help="the submission's top-level "
                                          "directory")
    parser.add_argument('-j', '--mip_era', help='the mip_era that data is '
                                                'ultimately being submitted to '
                                                '(default: %(default)s)',
                        default='CMIP6')
    parser.add_argument('-f', '--file-format', help='the CMOR version of the '
                                                    'input netCDF files being '
                                                    'submitted (CMIP5 or CMIP6)'
                                                    ' (default: %(default)s)',
                        default='CMIP6')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output', help='write the new entries to the '
                                              'JSON file specified rather '
                                              'than to the database', type=str)
    group.add_argument('-i', '--input', help='read the entries to add to the '
                                             'database from the JSON file '
                                             'specified rather than by '
                                             'validating files', type=str)
    parser.add_argument('-t', '--tape-base-url', help='add a tape url to each '
        'file with the base being specified on the command line', type=str)
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('-p', '--processes', help='the number of parallel processes '
        'to use (default: %(default)s)', default=8, type=int)
    parser.add_argument('-s', '--version-string', help='an optional version to '
        'use on all files. If not specifed the string in the incoming '
        'directory name or the current date is used', type=str)
    parser.add_argument('-r', '--relaxed', help='create a submission from '
        'validated files, ignoring failed files (default behaviour is to only '
        'create a submission when all files pass validation)', action='store_true')
    parser.add_argument('-v', '--validate_only', help='only validate the input, '
        'do not create a data submission', action='store_true')
    parser.add_argument('-n', '--no-prepare', help="don't run PrePARE",
                        action='store_true')
    parser.add_argument('-d', '--data-limit', help='the maximum size of file '
                                                   '(in bytes) to load into '
                                                   'memory for an HDF '
                                                   'integrity check (default: '
                                                   '%(default)s)',
                        type=int, default=MAX_DATA_INTEGRITY_SIZE)
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    if args.processes == 1 and not iris.__version__.startswith('1.'):
        # if not multiprocessing then limit the number of Dask threads
        # this can't seem to be limited when using multiprocessing
        dask.config.set(pool=ThreadPool(2))

    submission_dir = os.path.normpath(args.directory)
    logger.debug('Submission directory: %s', submission_dir)
    logger.debug('Project: %s', args.mip_era)
    logger.debug('Processes requested: %s', args.processes)

    try:
        if args.input:
            validated_metadata = read_json_file(args.input)
            data_sub = _get_submission_object(submission_dir)
            files_online = False
        else:
            files_online = True
            data_files = list_files(submission_dir)

            logger.debug('%s files identified', len(data_files))

            if not args.validate_only and not args.output:
                data_sub = _get_submission_object(submission_dir)

                if data_sub.status != 'ARRIVED':
                    msg = "The submission's status is not ARRIVED."
                    logger.error(msg)
                    raise SubmissionError(msg)

            try:
                if not args.no_prepare:
                    run_prepare(data_files, args.processes)
                validated_metadata = list(identify_and_validate(data_files,
                    args.mip_era, args.processes, args.file_format))
            except SubmissionError:
                if not args.validate_only and not args.output:
                    send_admin_rejection_email(data_sub)
                raise

            logger.debug('%s files validated successfully',
                         len(validated_metadata))

            if args.validate_only:
                logger.debug('Data submission not run (-v option specified)')
                logger.debug('Processing complete')
                sys.exit(0)

            if not args.relaxed and len(validated_metadata) != len(data_files):
                # if not args.output:
                #     rejected_dir = move_rejected_files(submission_dir)
                #     set_status_rejected(data_sub, rejected_dir)
                #     send_user_rejection_email(data_sub)
                msg = ('Not all files passed validation. Please fix these '
                       'errors and then re-run this script.')
                logger.error(msg)
                raise SubmissionError(msg)

        if args.tape_base_url:
            add_tape_url(validated_metadata, args.tape_base_url, submission_dir)

        if args.output:
            write_json_file(validated_metadata, args.output)
        else:
            update_database_submission(validated_metadata, data_sub,
                                       files_online, args.version_string)
            logger.debug('%s files submitted successfully',
                match_one(DataSubmission, incoming_directory=submission_dir).get_data_files().count())

    except SubmissionError:
        sys.exit(1)

    logger.debug('Processing complete')


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    if cmd_args.log_level:
        try:
            log_level = getattr(logging, cmd_args.log_level.upper())
        except AttributeError:
            logger.setLevel(logging.WARNING)
            logger.error('log-level must be one of: debug, info, warn or error')
            sys.exit(1)
    else:
        log_level = DEFAULT_LOG_LEVEL

    # configure the logger
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_LOG_FORMAT,
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })

    # run the code
    main(cmd_args)
