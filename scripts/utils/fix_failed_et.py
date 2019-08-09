#!/usr/bin/env python
"""
fix_failed_et.py

Elastic tape retrievals occasionally fail when a significant way through a
large retrieval. This script identfies files in this specified
retrieval, checks their checksum and if they are fine then copies them into
the DRS directory structure and updates the file's status in the DMT.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import DataFile, Settings
from pdata_app.utils.common import (adler32, construct_drs_path,
                                    get_gws_any_dir, ilist_files)

__version__ = '0.1.0b'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Check extracted data and '
                                                 'move to DRS.')
    parser.add_argument('top_dir', help='The top-level directory to search '
                                        'for files')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """Main entry point"""
    base_dir = Settings.get_solo().base_output_dir

    for extracted_file in ilist_files(args.top_dir):
        found_name = os.path.basename(extracted_file)

        try:
            data_file = DataFile.objects.get(name=found_name)
        except django.core.exceptions.ObjectDoesNotExist:
            logger.warning('Cannot find DMT entry. Skipping {}'.
                           format(extracted_file))
            continue

        found_checksum = adler32(extracted_file)
        if not found_checksum == data_file.checksum_set.first().checksum_value:
            logger.warning("Checksum doesn't match. Skipping {}".
                           format(found_name))
            continue

        dest_dir = os.path.join(get_gws_any_dir(extracted_file), 'stream1',
                                construct_drs_path(data_file))
        dest_path = os.path.join(dest_dir, found_name)
        if os.path.exists(dest_path):
            logger.warning('Skipping {} as it already exists at {}'.
                           format(found_name, dest_path))
            continue
        # create the directory if it doesn't exist
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        os.rename(extracted_file, dest_path)

        # create a link from the base dir
        link_dir = os.path.join(base_dir, construct_drs_path(data_file))
        link_path = os.path.join(link_dir, data_file.name)
        if not  os.path.exists(link_dir):
            os.makedirs(link_dir)
        os.symlink(dest_path, link_path)

        data_file.online = True
        data_file.directory = dest_dir
        data_file.save()


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
