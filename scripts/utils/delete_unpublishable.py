#!/usr/bin/env python
"""
delete_unpublishable.py

Remove from disk any datasets that cannot be published. They will remain in the
DMT and on tape and so can be restored to disk again if required.
"""
import argparse
import logging.config

import django
django.setup()
from pdata_app.models import DataRequest, Settings  # nopep8
from pdata_app.utils.common import delete_files  # nopep8

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Delete unpublishable')
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
    eday_snw = DataRequest.objects.filter(
        variable_request__table_name='Eday',
        variable_request__cmor_name='snw',
        datafile__isnull=False
    )

    lmon_mrlsl = DataRequest.objects.filter(
        variable_request__table_name='Lmon',
        variable_request__cmor_name='mrlsl',
        datafile__isnull=False
    )

    omon_msftmyz = DataRequest.objects.filter(
        variable_request__table_name='Omon',
        variable_request__cmor_name='msftmyz',
        datafile__isnull=False
    )

    primsiday_siuv = DataRequest.objects.filter(
        variable_request__table_name='PrimSIday',
        variable_request__cmor_name__in=['siu', 'siv'],
        datafile__isnull=False
    )

    simon_siflsaltbot = DataRequest.objects.filter(
        variable_request__table_name='SImon',
        variable_request__cmor_name='siflsaltbot',
        datafile__isnull=False
    )

    awi = DataRequest.objects.filter(
        institute__short_name='AWI',
        datafile__isnull=False
    )

    dreqs = (eday_snw | lmon_mrlsl | omon_msftmyz | primsiday_siuv |
             simon_siflsaltbot | awi)

    logger.info(f'{dreqs.count()} data requests to delete')

    for dreq in dreqs:
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
