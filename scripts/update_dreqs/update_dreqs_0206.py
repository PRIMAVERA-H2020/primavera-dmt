#!/usr/bin/env python
"""
update_dreqs_0206.py

ESGF

Retrigger Cylc tasks for ESGF datasets that have previously failed.
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import argparse
import logging.config
import sys

import django
django.setup()

from pdata_app.models import ESGFDataset
from pdata_app.utils.common import run_command, construct_cylc_task_name

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
    bad_sets = ESGFDataset.objects.filter(
        status__in=['CREATED', 'NOT_ON_DISK'],
        data_request__climate_model__short_name='HadGEM3-GC31-LL',
        data_request__experiment__short_name='control-1950',
        data_request__rip_code='r1i1p1f1',
    ).distinct()

    logger.debug(f'{bad_sets.count()} data sets found')

    for bad_set in bad_sets:
        task_id = construct_cylc_task_name(bad_set, 'crepp_submission')
        run_command(f'cylc trigger u-av973 {task_id}')


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
