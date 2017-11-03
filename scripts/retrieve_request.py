#!/usr/bin/env python2.7
"""
retrieve_request.py

This script is run by the admin to perform a retrieval request.
"""
import argparse
import datetime
import glob
from itertools import chain
import logging.config
from multiprocessing import Process, Manager
import os
import random
import shutil
import subprocess
import sys
import time

import cf_units

import django
django.setup()
from django.contrib.auth.models import User
from django.utils import timezone

from pdata_app.models import Settings, RetrievalRequest, DataFile, EmailQueue
from pdata_app.utils.common import (md5, sha256, adler32, construct_drs_path,
                                    get_temp_filename)
from pdata_app.utils.dbapi import match_one


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir
# The name of the directory to store et_get.py log files in
LOG_FILE_DIR = '/group_workspaces/jasmin2/primavera5/.et_logs/'
# The prefix to use on et_get.py log files
LOG_PREFIX = 'et_get'
# The number of processes that et_get.py should use.
# Between 5 and 10 are recommended
MAX_ET_GET_PROC = 10
# The maximum number of MASS retrievals to run in parallel
MAX_MOOSE_GET_PROC = 10

class ChecksumError(Exception):
    def __init__(self, message=''):
        """
        An exception to indicate that a data file's checksum does not match
        the value recorded in the database.

        :param str message: The error message text.
        """
        Exception.__init__(self)
        self.message = message


def parallel_get_urls(tapes, args):
    """
    Get several tape URLs in parallel so that MOOSE can group retrievals
    together to minimise the number of tape loads.

    :param dict tapes: The keys are the tape URLs to retrieve. The values are
        a list of DataFile objects to retrieve for that URL.
    :param argparse.Namespace args: The parsed command line arguments
        namespace.
    """
    jobs = []
    manager = Manager()
    params = manager.Queue()
    for i in range(MAX_MOOSE_GET_PROC):
        p = Process(target=parallel_worker, args=(params,))
        jobs.append(p)
        p.start()

    tape_urls_list = [(tape_url, tapes[tape_url], args) for tape_url in tapes]

    null_arguments = (None, None, None)
    iters = chain(tape_urls_list,  (null_arguments,) * MAX_MOOSE_GET_PROC)
    for iter in iters:
        params.put(iter)

    for j in jobs:
        j.join()


def parallel_worker(params):
    """
    The worker function that unpacks the parameters and calls the usual
    serial function.

    :param multiprocessing.Manager.Queue params: the queue to get function
        call parameters from
    """
    while True:
        # close existing connections so that a fresh connection is made
        django.db.connections.close_all()

        tape_url, data_files, args = params.get()

        if tape_url is None:
            return

        get_tape_url(tape_url, data_files, args)


def get_tape_url(tape_url, data_files, args):
    """
    Get all of the data from `tape_url`.

    :param str tape_url: The URL of the tape data to fetch.
    :param list data_files: DataFile objects corresponding to the data files
        required.
    :param argparse.Namespace args: The parsed command line arguments
        namespace.
    """
    if tape_url.startswith('et:'):
        get_et_url(tape_url, data_files, args)
    elif tape_url.startswith('moose:'):
        get_moose_url(tape_url, data_files, args)
    else:
        msg = ('Tape url {} is not a currently supported type of tape.'.
               format(tape_url))
        logger.error(msg)
        raise NotImplementedError(msg)


def get_moose_url(tape_url, data_files, args):
    """
    Get all of the data from `tape_url`, which is already known to be a MOOSE
    url. Data is not cached and is instead copied directly into the destination
    directory.

    :param str tape_url: The url to fetch
    :param list data_files: The DataFile objects to retrieve
    :param argparse.Namespace args: The parsed command line arguments
        namespace.
    """
    logger.debug('Starting restoring {}'.format(tape_url))

    # because the PRIMAVERA data that has been stored in MASS is in a DRS
    # directory structure already then all files that have an identical
    # tape_url will be placed in the same output directory
    drs_path = construct_drs_path(data_files[0])
    if not args.alternative:
        drs_dir = os.path.join(BASE_OUTPUT_DIR, drs_path)
    else:
        drs_dir = os.path.join(args.alternative, drs_path)

    # create the path if it doesn't exist
    if not os.path.exists(drs_dir):
        try:
            os.makedirs(drs_dir)
        except OSError:
            # if running in parallel, another process could have created this
            # directory at the same time and so wait a random time less than
            # one second. If it fails a second time then there is a genuine
            # problem
            time.sleep(random.random())
            if not os.path.exists(drs_dir):
                os.makedirs(drs_dir)

    moose_urls = ['{}/{}'.format(tape_url, df.name) for df in data_files]
    cmd = 'moo get -I {} {}'.format(' '.join(moose_urls), drs_dir)

    logger.debug('MOOSE command is:\n{}'.format(cmd))

    try:
        cmd_out = _run_command(cmd)
    except RuntimeError as exc:
        logger.error('MOOSE command failed\n{}'.
                     format(exc.message))
        sys.exit(1)

    logger.debug('Restored {}'.format(tape_url))

    _remove_data_license_files(drs_dir)

    for data_file in data_files:
        if not args.skip_checksums:
            try:
                _check_file_checksum(data_file,
                                     os.path.join(drs_dir, data_file.name))
            except ChecksumError:
                # warning message has already been displayed and so take no
                # further action
                pass

        # create symbolic link from main directory if storing data in an
        # alternative directory
        if args.alternative:
            primary_path = os.path.join(BASE_OUTPUT_DIR, drs_path)
            if not os.path.exists(primary_path):
                os.makedirs(primary_path)
            os.symlink(os.path.join(drs_dir, data_file.name),
                       os.path.join(primary_path, data_file.name))

        data_file.directory = drs_dir
        data_file.online = True
        try:
            data_file.save()
        except django.db.utils.IntegrityError:
            logger.error('data_file.save() failed for {} {}'.format(data_file.directory, data_file.name))
            raise


def get_et_url(tape_url, data_files, args):
    """
    Get all of the data from `tape_url`, which is already known to be an ET url.

    :param str tape_url: The url to fetch
    :param list data_files: The files to retrieve
    :param argparse.Namespace args: The parsed command line arguments
        namespace.
    """
    logger.debug('Starting restoring {}'.format(tape_url))

    # make a file containing the paths of the files to retrieve from tape
    filelist_name = get_temp_filename('et_files.txt')
    with open(filelist_name, 'w') as fh:
        for data_file in data_files:
            fh.write(os.path.join(data_file.incoming_directory, data_file.name)
                     + '\n')
    logger.debug('File list written to {}'.format(filelist_name))

    if not args.alternative:
        retrieval_dir = os.path.normpath(
            os.path.join(BASE_OUTPUT_DIR, '..', '.et_retrievals',
            'ret_{:04}'.format(args.retrieval_id)))
    else:
        retrieval_dir = os.path.normpath(
            os.path.join(args.alternative, '..', '.et_retrievals',
            'ret_{:04}'.format(args.retrieval_id)))

    if not os.path.exists(retrieval_dir):
        os.makedirs(retrieval_dir)

    logger.debug('Restoring to {}'.format(retrieval_dir))

    cmd = 'et_get.py -v -l {} -f {} -r {} -t {}'.format(
        _make_logfile_name(LOG_FILE_DIR), filelist_name, retrieval_dir,
        MAX_ET_GET_PROC)

    logger.debug('et_get.py command is:\n{}'.format(cmd))

    try:
        cmd_out = _run_command(cmd)
        pass
    except RuntimeError as exc:
        logger.error('et_get.py command failed\n{}'.format(exc.message))
        sys.exit(1)

    copy_et_files_into_drs(data_files, retrieval_dir, args)

    try:
        os.remove(filelist_name)
    except OSError:
        logger.warning('Unable to delete temporary file: {}'.
                       format(filelist_name))

    try:
        shutil.rmtree(retrieval_dir)
    except OSError:
        logger.warning('Unable to delete retrieval directory: {}'.
                       format(retrieval_dir))

    logger.debug('Restored {}'.format(tape_url))


def copy_et_files_into_drs(data_files, retrieval_dir, args):
    """
    Copy files from the restored data cache into the DRS structure.

    :param list data_files: The DataFile objects to copy.
    :param str retrieval_dir: The path that the files were retrieved to.
    :param argparse.Namespace args: The parsed command line arguments
        namespace.
    """
    logger.debug('Copying elastic tape files')

    for data_file in data_files:
        file_submission_dir = data_file.incoming_directory
        extracted_file_path = os.path.join(retrieval_dir,
                                           file_submission_dir.lstrip('/'),
                                           data_file.name)
        if not os.path.exists(extracted_file_path):
            msg = ('Unable to find file {} in the extracted data at {}. The '
                   'expected path was {}'.format(data_file.name, retrieval_dir,
                                                 extracted_file_path))
            logger.error(msg)
            sys.exit(1)

        drs_path = construct_drs_path(data_file)
        if not args.alternative:
            drs_dir = os.path.join(BASE_OUTPUT_DIR, drs_path)
        else:
            drs_dir = os.path.join(args.alternative, drs_path)
        dest_file_path = os.path.join(drs_dir, data_file.name)

        # create the path if it doesn't exist
        if not os.path.exists(drs_dir):
            os.makedirs(drs_dir)

        if os.path.exists(dest_file_path):
            msg = 'File already exists on disk: {}'.format(dest_file_path)
            logger.warning(msg)
        else:
            os.rename(extracted_file_path, dest_file_path)

        if not args.skip_checksums:
            try:
                _check_file_checksum(data_file, dest_file_path)
            except ChecksumError:
                # warning message has already been displayed and so take no
                # further action
                pass

        # create symbolic link from main directory if storing data in an
        # alternative directory
        if args.alternative:
            primary_path = os.path.join(BASE_OUTPUT_DIR, drs_path)
            if not os.path.exists(primary_path):
                os.makedirs(primary_path)
            os.symlink(dest_file_path,
                       os.path.join(primary_path, data_file.name))

        # set directory and set status as being online
        data_file.directory = drs_dir
        data_file.online = True
        data_file.save()

    logger.debug('Finished copying elastic tape files')


def _check_file_checksum(data_file, file_path):
    """
    Check that a restored file's checksum matches the value in the database.

    :param pdata_app.models.DataFile data_file: the database file object
    :param str file_path: the path to the restored file
    :raises ChecksumError: if the checksums don't match.
    """
    checksum_methods = {'ADLER32': adler32,
                        'MD5': md5,
                        'SHA256': sha256}

    # there is only likely to be one checksum and so chose the last one
    checksum_obj = data_file.checksum_set.last()

    if not checksum_obj:
        msg = ('No checksum exists in the database. Skipping check for {}'.
               format(file_path))
        logger.warning(msg)
        return

    file_checksum = checksum_methods[checksum_obj.checksum_type](file_path)

    if file_checksum != checksum_obj.checksum_value:
        msg = ('Checksum for restored file does not match its value in the '
               'database.\n {}: {}:{}\nDatabase: {}:{}'.format(file_path,
               checksum_obj.checksum_type, file_checksum,
               checksum_obj.checksum_type, checksum_obj.checksum_value))
        logger.warning(msg)
        raise ChecksumError(msg)


def _make_logfile_name(directory=None):
    """
    From the current date and time make a filename for a log-file.

    :param str directory: The optional directory path to prepend to the
        generated filename
    :returns: The name of a log file to use
    """
    time_str = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = '{}_{}.txt'.format(LOG_PREFIX, time_str)
    if directory:
        return os.path.join(directory, filename)
    else:
        return filename


def _run_command(command):
    """
    Run the command specified and return any output to stdout or stderr as
    a list of strings.
    :param str command: The complete command to run.
    :returns: Any output from the command as a list of strings.
    :raises RuntimeError: If the command did not complete successfully.
    """
    cmd_out = None
    try:
        cmd_out = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                          shell=True)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 17:
            pass
        else:
            msg = ('Command did not complete sucessfully.\ncommmand:\n{}\n'
                   'produced error:\n{}'.format(command, exc.output))
            logger.warning(msg)
            raise RuntimeError(msg)

    if isinstance(cmd_out, str):
        return cmd_out.rstrip().split('\n')
    else:
        return None


def _email_user_success(retrieval):
    """
    Send an email to request's creator advising them that their data's been
    successfully restored.

    :param pdata_app.models.RetrievalRequest retrieval: the retrieval object
    """
    contact_user_id = Settings.get_solo().contact_user_id
    contact_user = User.objects.get(username=contact_user_id)

    msg = (
        'Dear {},\n'
        '\n'
        'Your retrieval request number {} has now been restored from '
        'tape to group workspace. The data will be available in the DRS '
        'directory structure at {}.\n'
        '\n'
        'To free up disk space on the group workspaces we would be grateful '
        'if this data could be marked as finished at '
        'https://prima-dm.ceda.ac.uk/retrieval_requests/ as soon as you have '
        'finished analysing it.\n'
        '\n'
        'Thanks,\n'
        '\n'
        '{}'.format(retrieval.requester.first_name, retrieval.id,
                    BASE_OUTPUT_DIR, contact_user.first_name)
    )

    _email = EmailQueue.objects.create(
        recipient=retrieval.requester,
        subject=('[PRIMAVERA_DMT] Retrieval Request {} Complete'.
                 format(retrieval.id)),
        message=msg
    )


def _remove_data_license_files(dir_path):
    """
    Delete any Met Office Data License files from the directory specified.

    :param str dir_path: The directory to remove files from.
    """
    license_file_glob = 'MetOffice_data_licence.*'

    for lic_file in glob.iglob(os.path.join(dir_path, license_file_glob)):
        try:
            os.remove(lic_file)
        except OSError:
            logger.warning('Unable to delete license file {}'.format(lic_file))


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Perform a PRIMAVERA '
                                                 'retrieval request.')
    parser.add_argument('retrieval_id', help='the id of the retrieval request '
        'to carry out.', type=int)
    parser.add_argument('-a', '--alternative', help="store data in alternative "
        "directory and create a symbolic link to each file from the main "
        "retrieval directory")
    parser.add_argument('-s', '--skip_checksums', help="don't check the "
        "checksums on restored files.", action='store_true')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    logger.debug('Starting retrieve_request.py')

    # check retrieval
    retrieval = match_one(RetrievalRequest, id=args.retrieval_id)
    if not retrieval:
        logger.error('Unable to find retrieval id {}'.format(
            args.retrieval_id))
        sys.exit(1)

    if retrieval.date_complete:
        logger.error('Retrieval {} was already completed, at {}.'.
                     format(retrieval.id,
                            retrieval.date_complete.strftime('%Y-%m-%d %H:%M')))
        sys.exit(1)

    tapes = {}
    for data_req in retrieval.data_request.all():
        all_files = data_req.datafile_set.all()
        time_units = all_files[0].time_units
        calendar = all_files[0].calendar
        start_float = cf_units.date2num(
            datetime.datetime(retrieval.start_year, 1, 1), time_units,
            calendar
        )
        end_float = cf_units.date2num(
            datetime.datetime(retrieval.end_year + 1, 1, 1), time_units,
            calendar
        )
        data_files = all_files.filter(start_time__gte=start_float,
                                      end_time__lt=end_float,
                                      online=False)

        tape_urls = [qs['tape_url'] for qs in data_files.values('tape_url')]

        tape_urls = list(set(tape_urls))
        tape_urls.sort()

        for tape_url in tape_urls:
            url_files = data_files.filter(tape_url=tape_url)
            if tape_url in tapes:
                tapes[tape_url] = list(chain(tapes[tape_url], url_files))
            else:
                tapes[tape_url] = list(url_files)

    all_moose = True
    for tape_url in tapes:
        if not tape_url.startswith('moose:'):
            all_moose = False

    if not all_moose:
        for tape_url in tapes:
            get_tape_url(tape_url, tapes[tape_url], args)
    else:
        # lets get parallel to speed things up
        parallel_get_urls(tapes, args)
        # get a fresh DB connection after exiting from parallel operation
        django.db.connections.close_all()


    # set date_complete in the db
    retrieval.date_complete = timezone.now()
    retrieval.save()

    # send an email to advise the user that their data's been restored
    _email_user_success(retrieval)

    logger.debug('Completed retrieve_request.py')


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
