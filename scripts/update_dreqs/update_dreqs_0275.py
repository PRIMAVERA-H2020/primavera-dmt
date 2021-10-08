#!/usr/bin/env python
"""
update_dreqs_0275.py

Delete from the DMT the replaced files and data requests that are preventing
ESGF publication for MOHC and NERC HadGEM3-GC31-HH.
"""
import argparse
import logging.config


import django
django.setup()

from pdata_app.models import DataRequest  # nopep8
from pdata_app.utils.common import filter_hadgem_stream2  # nopep8
__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def _remove_hh_dreq(dreq):
    """
    Check that the data request doesn't have any data files referencing it,
    then remove any replaced files and finally delete the data request.
    """
    if dreq.datafile_set.count() != 0:
        logger.error('Data request %s has files associated with it.', dreq)
    else:
        dreq.replacedfile_set.all().delete()
        dreq.delete()


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Create retrieval requests')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='info')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main():
    """
    Main entry point
    """
    hist_mon_day = filter_hadgem_stream2(DataRequest.objects.filter(
        institute__short_name='MOHC',
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name='hist-1950',
        variable_request__frequency__in=['mon', 'day', '3hr'],
        rip_code='r1i1p1f1'
    ))

    ctrl_3hr = DataRequest.objects.filter(
        institute__short_name='NERC',
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name='control-1950',
        variable_request__table_name__in=['3hr', 'E3hrPt']
    ).distinct()

    ctrl_mon_day = filter_hadgem_stream2(DataRequest.objects.filter(
        institute__short_name='NERC',
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name='control-1950',
        variable_request__frequency__in=['mon', 'day'],
        rip_code='r1i1p1f1'
    ))

    dreqs = (hist_mon_day | ctrl_mon_day | ctrl_3hr)

    logger.info('%s data requests found', dreqs.count())

    for dreq in dreqs:
        _remove_hh_dreq(dreq)


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
    main()
