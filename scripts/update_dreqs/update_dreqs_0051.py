#!/usr/bin/env python2.7
"""
update_dreqs_0051.py

Remove the existing files for 1979 for the onm and ind streams from
HadGEM3-GC31-MM spinup-1950.
"""
import argparse
import logging.config
import os
import sys

from cf_units import date2num, CALENDAR_GREGORIAN

import django
django.setup()
from pdata_app.models import DataFile
from pdata_app.utils.replace_file import replace_files



__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


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
    tables_to_delete = ['SIday', 'PrimSIday', 'Omon', 'PrimOmon']
    deletion_files = DataFile.objects.filter(
        data_request__climate_model__short_name='HadGEM3-GC31-MM',
        data_request__experiment__short_name='spinup-1950',
        variable_request__table_name__in=tables_to_delete,
        name__contains='1979'
    ).exclude(name__contains='siconc_SIday')

    logger.debug('{} files'.format(deletion_files.count()))
    for df in deletion_files:
        logger.debug(df.name)

    replace_files(deletion_files)


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
