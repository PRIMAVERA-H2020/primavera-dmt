#!/usr/bin/env python
"""
update_dreqs_0322.py

ESGF AttributeUpdate
Called from a Rose suite to update the directory in early CERFACS datasets.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()

from pdata_app.models import DataFile, DataRequest, Settings  # nopep8
from pdata_app.utils.attribute_update import CorrectDirectoryUpdate  # nopep8
from pdata_app.utils.common import adler32, delete_files  # nopep8


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Update filename')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('request_id', help='to request id to update')
    parser.add_argument('-s', '--skip-checksum', help='skip deleting failed '
                                                      'checksums',
                        action = 'store_true')
    parser.add_argument('-t', '--totally-skip', help='skip checksums',
                        action = 'store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    model, expt, var_lab, table, var = args.request_id.split('_')

    dreq = DataRequest.objects.get(
        climate_model__short_name=model,
        experiment__short_name=expt,
        rip_code=var_lab,
        variable_request__table_name=table,
        variable_request__cmor_name=var
    )
    logger.debug('DataRequest is {}'.format(dreq))

    if not args.totally_skip:
        logger.debug('Checking checksums')
        checksum_mismatch = 0
        for data_file in dreq.datafile_set.order_by('name'):
            logger.debug('Checking {}'.format(data_file.name))
            full_path = os.path.join(data_file.directory, data_file.name)
            actual = adler32(full_path)
            expected = data_file.checksum_set.first().checksum_value
            if actual != expected:
                logger.error(f'Checksum mismatch for {full_path}')
                checksum_mismatch += 1
                if not args.skip_checksum:
                    dfs = DataFile.objects.filter(name=data_file.name)
                    if dfs.count() != 1:
                        logger.error(f'Unable to select file for deletion {full_path}')
                    else:
                        delete_files(dfs.all(), BASE_OUTPUT_DIR)
        if checksum_mismatch:
            logger.error(f'Exiting due to {checksum_mismatch} checksum failures.')
            logger.error(f'Data request is in {dreq.directories()}')
            sys.exit(1)

    logger.debug('Processing files')
    for data_file in dreq.datafile_set.order_by('name'):
        logger.debug('Processing {}'.format(data_file.name))

        updater = CorrectDirectoryUpdate(data_file)
        updater.update()


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    log_level = getattr(logging, cmd_args.log_level.upper())

    # configure the logger
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(levelname)s: %(message)s',
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
