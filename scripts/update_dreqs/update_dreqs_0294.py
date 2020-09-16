#!/usr/bin/env python
"""
update_dreqs_0294.py

Move the CMMC-CM2-VHR4 control-1950 data from the CEDA archives to the
correct path in the PRIMAVERA group workspaces. This overcomes a bug in
update_dreqs_0288.py
"""
import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()
from pdata_app.models import DataFile  # nopep8
from pdata_app.utils.common import construct_drs_path  # nopep8

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

BASE_GWS = '/gws/nopw/j04/primavera4/stream1'
ARCHIVE_BASE = '/badc/cmip6'


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    affected_files = DataFile.objects.filter(
        climate_model__short_name='CMCC-CM2-VHR4',
        experiment__short_name='control-1950',
        variable_request__table_name__in=['6hrPlev', '6hrPlevPt', 'Amon',
                                          'day', 'LImon', 'Lmon', 'Oday',
                                          'Omon', 'SIday', 'SImon']
    ).exclude(
        variable_request__table_name='6hrPlevPt',
        variable_request__cmor_name='psl'
    ).distinct().order_by(
        'variable_request__table_name', 'variable_request__cmor_name'
    )

    num_files = affected_files.count()
    logger.debug(f'{num_files} affected files found')

    for df in affected_files:
        bad_dir = os.path.join(df.directory, df.name)
        bad_path = os.path.join(bad_dir, df.name)
        if not os.path.exists(bad_path):
            logger.error(f'Could not find {df.name} ')
            continue
        temp_path = os.path.join(df.directory, df.name) + '.tmp'
        try:
            os.rename(bad_path, temp_path)
            os.rmdir(bad_dir)
            os.rename(temp_path, os.path.join(df.directory, df.name))
        except OSError as exc:
            logger.error(f'{df.name} {exc}')


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
