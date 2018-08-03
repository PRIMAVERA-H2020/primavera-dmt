#!/usr/bin/env python
"""
update_dreqs_0072.py

This script creates new source_ids for EC-Earth3P and updates existing coupled
data requests to use these new source_ids.
"""
from __future__ import unicode_literals, division, absolute_import
import argparse
import logging.config
import sys

import django
django.setup()
from pdata_app.models import ClimateModel, DataRequest

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
    lr = ClimateModel.objects.create(short_name='EC-Earth3P',
                                     full_name='EC-Earth3P')
    hr = ClimateModel.objects.create(short_name='EC-Earth3P-HR',
                                     full_name='EC-Earth3P-HR')

    num_updated = DataRequest.objects.filter(
        climate_model__short_name='EC-Earth3',
        experiment__short_name__in=['control-1950', 'highres-future',
                                    'hist-1950', 'spinup-1950',
                                    'highresSST-future']
    ).update(climate_model=lr)

    logger.debug('{} DataRequests updated to use {}'.format(num_updated, lr))

    num_updated = DataRequest.objects.filter(
        climate_model__short_name='EC-Earth3-HR',
        experiment__short_name__in=['control-1950', 'highres-future',
                                    'hist-1950', 'highresSST-future']
    ).update(climate_model=hr)

    logger.debug('{} DataRequests updated to use {}'.format(num_updated, hr))


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
