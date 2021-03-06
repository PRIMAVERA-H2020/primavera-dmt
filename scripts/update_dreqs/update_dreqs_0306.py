#!/usr/bin/env python
"""
update_dreqs_0306.py

Correct the institute on epfz for HadGEM3-GC31-HH hist-1950 and
control-1950.
"""
import argparse
import logging.config
import sys

import django
django.setup()
from pdata_app.models import DataRequest, Institute

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
    # hist-1950
    hist_dreqs = DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name='hist-1950',
        variable_request__cmor_name='epfz'
    )
    nerc = Institute.objects.get(short_name='NERC')

    num_dreqs = hist_dreqs.count()
    expected = 2
    msg = f'{num_dreqs} affected data requests found for hist-1950'
    if num_dreqs != expected:
        raise ValueError(msg)
    logger.debug(msg)

    hist_dreqs.update(institute=nerc)

    # control-1950
    ctrl_dreqs = DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name='control-1950',
        variable_request__cmor_name='epfz'
    )
    mohc = Institute.objects.get(short_name='MOHC')

    num_dreqs = ctrl_dreqs.count()
    expected = 2
    msg = f'{num_dreqs} affected data requests found for control-1950'
    if num_dreqs != expected:
        raise ValueError(msg)
    logger.debug(msg)

    ctrl_dreqs.update(institute=mohc)


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
