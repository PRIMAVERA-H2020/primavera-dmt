#!/usr/bin/env python
"""
update_dreqs_0293.py

Copy the new July 1982 CMMC-CM2-VHR4 control-1950 data into the directory
structure.
"""
import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()
from pdata_app.models import DataFile, DataRequest  # nopep8
from pdata_app.utils.common import construct_drs_path  # nopep8

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

BASE_INCOMING_DIR = '/gws/nopw/j04/primavera5/upload/CMCC/20200427'

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
    dreqs = DataRequest.objects.filter(
        climate_model__short_name='CMCC-CM2-VHR4',
        experiment__short_name='control-1950',
        datafile__isnull=False
    ).exclude(
        variable_request__table_name__in=['LImon', 'Lmon', 'Oday', 'Omon', 
                                          'PrimOday', 'PrimOmon', 'SIday', 
                                          'SImon']
    ).distinct().order_by(
        'variable_request__table_name', 'variable_request__cmor_name'
    )

    num_dreqs = dreqs.count()
    logger.info(f'{num_dreqs} data requests found')

    for dreq in dreqs:
        try:
            df = dreq.datafile_set.get(name__contains='198207')
        except django.core.exceptions.ObjectDoesNotExist:
            logger.error(f'{dreq} no files found in DMT')
            continue
        logger.debug(f'Replacing {df.name}')
        file_name = df.name
        old_path = df.directory
        drs_path = construct_drs_path(df)
        new_path = os.path.join(BASE_INCOMING_DIR, drs_path, file_name)
        if not os.path.exists(new_path):
            logger.error(f'{new_path} not found')


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
