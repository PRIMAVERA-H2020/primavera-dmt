#!/usr/bin/env python
"""
update_dreqs_0274.py

Create a retrieval request for data that's required for ESGF publication for 
MOHC and NERC HadGEM3-GC31-HH.
"""
import argparse
import datetime
import logging.config
import sys


import django
django.setup()
from django.template.defaultfilters import filesizeformat

from django.contrib.auth.models import User
from pdata_app.models import RetrievalRequest, DataRequest
from pdata_app.utils.common import get_request_size, filter_hadgem_stream2

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Create retrieval requests')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='info')
    parser.add_argument('-c', '--create', help='Create the retrieval request '
                                               'rather than just displaying '
                                               'the data volums',
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    start_year = 1948
    end_year = 2051

    # data_reqs = filter_hadgem_stream2(DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-HH',
    #     experiment__short_name='highres-future',
    #     # variable_request__frequency__in=['3hr'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='O'
    # ).exclude(
    #     variable_request__table_name__startswith='SI'
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct())

    data_reqs = filter_hadgem_stream2(DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-MH',
        experiment__short_name='spinup-1950',
        variable_request__table_name__in=['SImon', 'SIday', 'PrimSIday'],
        datafile__isnull=False
    ).distinct())

    logger.info('Total data volume: {} Volume to restore: {}'.format(
        filesizeformat(get_request_size(data_reqs, start_year, end_year)).
            replace('\xa0', ' '),
        filesizeformat(get_request_size(data_reqs, start_year, end_year,
                                        offline=True)).replace('\xa0', ' '),
    ))

    if args.create:
        jon = User.objects.get(username='jseddon')
        rr = RetrievalRequest.objects.create(requester=jon, start_year=start_year,
                                             end_year=end_year)
        time_zone = datetime.timezone(datetime.timedelta())
        rr.date_created = datetime.datetime(2000, 1, 1, 0, 0, tzinfo=time_zone)
        rr.save()

        rr.data_request.add(*data_reqs)

        logger.info('Retrieval request {} created.'.format(rr.id))


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
    main(cmd_args)
