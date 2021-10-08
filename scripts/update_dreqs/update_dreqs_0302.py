#!/usr/bin/env python
"""
update_dreqs_0302.py

Create a retrieval request for data that's required for ESGF publication for 
EC-Earth PRIMAVERA specific.
"""
import argparse
import datetime
import logging.config


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
                        default='warning')
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
    end_year = 2101

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     experiment__short_name='highres-future',
    #     rip_code='r1i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='highres-future',
    #     rip_code='r2i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='highres-future',
    #     rip_code='r3i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     # climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     # climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r3i1p1f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r2i1p1f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P-HR',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P-HR',
    #     experiment__short_name='control-1950',
    #     rip_code='r3i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='EC-Earth-Consortium',
    #     climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='spinup-1950',
    #     # rip_code='r3i1p2f1',
    #     variable_request__table_name__startswith='Prim',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    data_reqs = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3',
        experiment__short_name='highresSST-present',
        rip_code='r1i1p1f1',
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    # TODO highresSST-present r1i1p1f1
    
    logger.debug('Total data volume: {} Volume to restore: {}'.format(
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

        logger.debug('Retrieval request {} created.'.format(rr.id))


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
