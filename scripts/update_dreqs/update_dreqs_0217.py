#!/usr/bin/env python
"""
update_dreqs_0217.py

Copy the MPI AMIP data that is about to be retracted to a single
directory structure that can be backed-up to tape.
"""
import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()
from pdata_app.models import ESGFDataset
from pdata_app.utils.common import construct_drs_path

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

TAPE_WRITE_DIR = '/gws/nopw/j04/primavera3/cache/jseddon/backup/'

def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
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
    datasets = ESGFDataset.objects.filter(
        data_request__institute__short_name='MPI-M',
        data_request__experiment__short_name='highresSST-present',
        status='PUBLISHED'
    )

    logger.debug(f'Found {datasets.count()} datasets')

    for dataset in datasets:
        for datafile in dataset.data_request.datafile_set.all():
            dest_dir = os.path.join(TAPE_WRITE_DIR,
                                    construct_drs_path(datafile))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy(
                os.path.join(datafile.directory, datafile.name),
                dest_dir
            )
        logger.debug(f'Copied {dataset}')


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
