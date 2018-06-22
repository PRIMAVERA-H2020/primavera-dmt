#!/usr/bin/env python
"""
db_netcdf_housekeeping.py

This script has two actions:

1. it scans through all files listed as being online in the database. It then
checks that each file actually exists on disk and if not updates the file's
online flag and directory.

2. it scans through the specified directory structure and checks that each
netCDF file found is marked as online and has the correct directory.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import os
import sys

import django
django.setup()

from pdata_app.models import DataFile, Settings
from pdata_app.utils.common import (ilist_files, construct_drs_path,
                                    is_same_gws)

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

# The top-level directory where output data is stored
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


def scan_database():
    """
    Start the scan of the database.
    """
    logger.debug('Starting database scan.')

    for data_file in DataFile.objects.filter(online=True).iterator():
        full_path = os.path.join(data_file.directory, data_file.name)
        if not os.path.exists(full_path):
            logger.warning('File cannot be found on disk, status changed to '
                           'offline: {}'.format(full_path))
            data_file.online = False
            data_file.directory = None
            data_file.save()
            continue

        if not is_same_gws(data_file.directory, BASE_OUTPUT_DIR):
            sym_link_dir = os.path.join(BASE_OUTPUT_DIR,
                                         construct_drs_path(data_file))
            sym_link_path = os.path.join(sym_link_dir,
                                         data_file.name)
            if not os.path.exists(sym_link_path):
                if not os.path.exists(sym_link_dir):
                    os.makedirs(sym_link_dir)
                os.symlink(full_path, sym_link_path)
                logger.warning('Created symlink for file {} from {}'.
                               format(data_file.name, sym_link_path))

    logger.debug('Completed database scan.')


def scan_file_structure(directory):
    """
    Start the scan of the file structure.

    :param str directory: the top level directory to scan
    """
    logger.debug('Starting file structure scan.')

    for nc_file in ilist_files(directory):
        nc_file_name = os.path.basename(nc_file)
        db_files = DataFile.objects.filter(name=nc_file_name)

        if db_files.count() == 0:
            logger.error('File not found in database: {}'.format(nc_file))
        elif db_files.count() > 1:
            logger.error('{} entries found in database for file: {}'.
                         format(db_files.count(), nc_file))
        else:
            db_file = db_files.first()

            # This will return false for broken symbolic links
            if not os.path.exists(nc_file):
                os.remove(nc_file)
                if db_file.directory:
                    db_path = os.path.join(db_file.directory, db_file.name)
                    if os.path.exists(db_path):
                        logger.warning('Replacing broken link for file {}'.
                                       format(db_file.name))
                        os.symlink(os.path.join(db_file.directory,
                                                db_file.name),
                                   nc_file)
                else:
                    logger.warning('Removing broken link for file {}'.
                                   format(db_file.name))
                    if db_file.online:
                        db_file.online = False
                        db_file.save()
                    continue

            db_file.refresh_from_db()
            if not db_file.online:
                logger.warning('File status changed to online: {}'.
                               format(nc_file))
                db_file.online = True
                db_file.save()

            actual_path = os.path.realpath(nc_file)
            actual_dir = os.path.dirname(actual_path)
            if db_file.directory != actual_dir:
                logger.warning('Directory for file {} changed from {} to {}'.
                               format(nc_file_name, db_file.directory,
                                      actual_dir))
                db_file.directory = actual_dir
                db_file.save()

    logger.debug('Completed file structure scan.')


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description="Scan the database and file "
                                                 "structure to make sure that "
                                                 "the two are synchronised.")
    parser.add_argument('-d', '--no-database', help='Do not scan the database.',
                        action='store_true')
    parser.add_argument('-f', '--no-file-structure', help='Do not scan the '
                                                          'file structure.',
                        action='store_true')
    parser.add_argument('-t', '--top-level', help='The top-level directory to '
                                                  'scan (default: %(default)s)',
                        default=BASE_OUTPUT_DIR)
    parser.add_argument('-l', '--log-level', help='set logging level to one '
                                                  'of debug, info, warn (the '
                                                  'default), or error')
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    logger.debug('Starting db_netcdf_housekeeping')

    if not args.no_file_structure:
        scan_file_structure(args.top_level)

    if not args.no_database:
        scan_database()

    logger.debug('Completed db_netcdf_housekeeping')


if __name__ == '__main__':
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
