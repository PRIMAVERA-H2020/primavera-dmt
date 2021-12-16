#!/usr/bin/env python
"""
delete_not_stream2.py

Remove from disk any HadGEM datasets that are from Stream 2 but aren't in the
Stream 2 data request. They will remain in the DMT and on tape and so can be
restored to disk again if required.
"""
import argparse
import logging.config

import django
django.setup()
from pdata_app.models import DataRequest, Settings  # nopep8
from pdata_app.utils.common import delete_files, exclude_hadgem_stream2  # nopep8

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Update mip_era')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main():
    """
    Main entry point
    """
    hh = DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-HH'
    ).distinct()

    lower_res = DataRequest.objects.filter(
        climate_model__short_name__startswith='HadGEM3-GC31'
    ).exclude(
        climate_model__short_name='HadGEM3-GC31-HH'
    ).exclude(
        rip_code='r1i1p1f1'
    ).distinct()

    all_dreqs = hh | lower_res

    dreqs = exclude_hadgem_stream2(all_dreqs)

    logger.info(f'{dreqs.count()} data requests to delete')

    for dreq in dreqs.order_by('climate_model__short_name',
                               'experiment__short_name', 'rip_code',
                               'variable_request__table_name',
                               'variable_request__cmor_name'):
        logger.debug(dreq)
        delete_files(dreq.datafile_set.all(), BASE_OUTPUT_DIR, skip_badc=True)


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
    main()
