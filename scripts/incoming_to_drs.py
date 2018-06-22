#!/usr/bin/env python
"""
incoming_to_drs.py

This script is run by the admin to copy data files from their incoming
directory into the common DRS structure.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()

from pdata_app.models import Settings, DataSubmission
from pdata_app.utils.common import is_same_gws


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


def construct_drs_path(data_file):
    """
    Make the CMIP6 DRS directory path for the specified file.

    :param pdata_app.models.DataFile data_file:
    :returns: A string containing the DRS directory structure
    """
    return os.path.join(
        data_file.project.short_name,
        data_file.activity_id.short_name,
        data_file.institute.short_name,
        data_file.climate_model.short_name,
        data_file.experiment.short_name,
        data_file.rip_code,
        data_file.variable_request.table_name,
        data_file.variable_request.cmor_name,
        data_file.grid,
        data_file.version
    )


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
        sys.exit(1)
    except django.core.exceptions.ObjectDoesNotExist:
        msg = ('No DataSubmissions have been found in the database for '
               'directory: {}.'.format(submission_dir))
        logger.error(msg)
        sys.exit(1)

    return data_sub


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Copy files from their'
        'incoming directory into the central DRS structure.')
    parser.add_argument('directory', help="the submission's top-level "
                                          "directory")
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('-a', '--alternative', help='store data in alternative '
        'directory and create a symbolic link to each file from the main '
        'retrieval directory')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    logger.debug('Starting incoming_to_drs.py')

    data_sub = _get_submission_object(os.path.normpath(args.directory))

    if not args.alternative:
        drs_base_dir = BASE_OUTPUT_DIR
    else:
        drs_base_dir = args.alternative

    errors_encountered = False

    for data_file in data_sub.datafile_set.all():
        # make full path of existing file
        existing_path = os.path.join(data_file.directory, data_file.name)

        # make full path of where it will live
        drs_sub_path = construct_drs_path(data_file)
        drs_dir = os.path.join(drs_base_dir, drs_sub_path)
        drs_path = os.path.join(drs_dir, data_file.name)

        # check the destination directory exists
        if not os.path.exists(drs_dir):
            os.makedirs(drs_dir)

        # link if on same GWS, or else copy
        this_file_error = False
        if is_same_gws(existing_path, drs_path):
            try:
                os.link(existing_path, drs_path)
            except OSError as exc:
                logger.error('Unable to link from {} to {}. {}'.
                             format(existing_path, drs_path, str(exc)))
                errors_encountered = True
                this_file_error = True
        else:
            try:
                shutil.copyfile(existing_path, drs_path)
            except IOError as exc:
                logger.error('Unable to copy from {} to {}. {}'.
                             format(existing_path, drs_path, str(exc)))
                errors_encountered = True
                this_file_error = True

        # update the file's location in the database
        if not this_file_error:
            data_file.directory = os.path.join(drs_base_dir, drs_sub_path)
            if not data_file.online:
                data_file.online = True
            data_file.save()

        # if storing the files in an alternative location, create a sym link
        # from the primary DRS structure to the file
        if args.alternative and not this_file_error:
            primary_path = os.path.join(BASE_OUTPUT_DIR, drs_sub_path)
            try:
                if not os.path.exists(primary_path):
                    os.makedirs(primary_path)

                os.symlink(drs_path, os.path.join(primary_path, data_file.name))
            except OSError as exc:
                logger.error('Unable to link from {} to {}. {}'.
                             format(drs_path,
                                    os.path.join(primary_path, data_file.name),
                                    str(exc)))
                errors_encountered = True

    # summarise what happened and keep the DB updated
    if not errors_encountered:
        data_sub.directory = drs_base_dir
        data_sub.save()
        logger.debug('All files copied with no errors. Data submission '
                     'incoming directory can be deleted.')
    else:
        logger.error('Errors were encountered. Please fix these before '
                     'deleting the incoming directory.')

    logger.debug('Completed incoming_to_drs.py')


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
