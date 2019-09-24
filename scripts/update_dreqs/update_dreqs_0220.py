#!/usr/bin/env python
"""
update_dreqs_0220.py

Update the version of the MPI highresSST-present files and move into the
correct directory if they're online.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import DataRequest
from pdata_app.utils.common import construct_drs_path, delete_drs_dir, get_gws

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

NEW_VERSION = 'v20190923'

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
    dreqs = DataRequest.objects.filter(
        climate_model__short_name__in=['MPI-ESM1-2-HR'], #'MPI-ESM1-2-XR'],
        experiment__short_name='highresSST-present',
        variable_request__table_name='Amon',
        variable_request__cmor_name='tas',
    )

    for dreq in dreqs:
        old_directories = []
        for df in dreq.datafile_set.order_by('name'):
            if not df.online:
                logger.error(f'Not online {df.name}')
                continue
            if df.version == NEW_VERSION:
                logger.warning(f'Already at {NEW_VERSION} {df.name}')
                continue
            df.version = NEW_VERSION
            gws = get_gws(df.directory)
            new_dir = os.path.join(gws, construct_drs_path(df))
            old_directory = df.directory
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            os.rename(os.path.join(df.directory, df.name),
                      os.path.join(new_dir, df.name))
            df.directory = new_dir
            df.save()
            if old_directory not in old_directories:
                old_directories.append(old_directory)

    for directory in old_directories:
        if not os.listdir(directory):
            delete_drs_dir(directory)
        else:
            logger.error(f'Not empty {directory}')


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
