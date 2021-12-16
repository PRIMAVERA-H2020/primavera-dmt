#!/usr/bin/env python
"""
delete_alevel.py

Remove from disk any EC-Earth datasets that are on atmosphere levels as these
cannot be published to the ESGF. They will remain in the DMT and on tape and
so can be restored to disk again if required.
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
    alevhalf = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        variable_request__dimensions__contains='alevhalf',
        datafile__isnull=False
    ).distinct()

    alevel = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        variable_request__dimensions__contains='alevel',
        datafile__isnull=False
    ).distinct()

    dreqs = alevhalf | alevel

    logger.debug(f'{dreqs.count()} data requests found')

    for dreq in dreqs.order_by('climate_model__short_name',
                               'experiment__short_name', 'rip_code',
                               'variable_request__table_name',
                               'variable_request__cmor_name'):
        if dreq.online_status() in ['online', 'partial']:
            logger.debug(dreq)
            delete_files(dreq.datafile_set.all(), BASE_OUTPUT_DIR,
                         skip_badc=True)


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
