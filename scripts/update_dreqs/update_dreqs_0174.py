#!/usr/bin/env python
"""
update_dreqs_0174.py

Create a retrieval request for data that's required for ESGF publication.
"""
from __future__ import unicode_literals, division, absolute_import
import argparse
import datetime
import logging.config
import sys


import django
django.setup()
from django.template.defaultfilters import filesizeformat

from django.contrib.auth.models import User
from pdata_app.models import RetrievalRequest, DataRequest
from pdata_app.utils.common import get_request_size

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Create retrieval requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
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

    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='MOHC',
    #     climate_model__short_name='HadGEM3-GC31-MM',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    # )
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['ECMWF-IFS-LR', 'ECMWF-IFS-HR'],
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )
    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='MOHC',
    #     climate_model__short_name='HadGEM3-GC31-MM',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    # )
    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='MOHC',
    #     climate_model__short_name='HadGEM3-GC31-HM',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    #     variable_request__frequency__in=['day']
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )# .exclude(
    #     variable_request__table_name='CFday'
    # )
    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='CMCC',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f2',
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )
    # data_reqs = DataRequest.objects.filter(
    #    climate_model__short_name='CNRM-CM6-1-HR',
    #    experiment__short_name='highresSST-present',
    #    rip_code='r1i1p1f2',
    #    variable_request__frequency__in=['mon', 'day', '6hr', '3hr'],
    #    datafile__isnull=False
    #).exclude(
    #    variable_request__table_name__startswith='Prim'
    #).distinct()
    # data_reqs = DataRequest.objects.filter(
    #      climate_model__short_name='HadGEM3-GC31-LL',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon', 
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday', 
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-LL',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon', 
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday', 
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['ECMWF-IFS-LR'],
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f1',
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-HM',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon', 
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday', 
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     # variable_request__frequency__in=['6hr', '3hr'],# 'mon', 'day', '6hr', '3hr', '1hr'],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-MM',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon', 
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday', 
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     # variable_request__frequency__in=['mon', 'day', '6hr'],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['ECMWF-IFS-HR'],
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # )
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1-HR',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f2',
    #     # variable_request__frequency__in=['mon', 'day', '6hr'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f2',
    #     # variable_request__frequency__in=['mon', 'day', '6hr'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='MPI-M',
    #     experiment__short_name='highresSST-present',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-LM',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'        
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-MM',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'        
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-HM',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name='CFday',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'        
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f2',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1-HR',
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f2',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CNRM-CM6-1-HR',
    #     experiment__short_name='highres-future',
    #     rip_code='r1i1p1f2',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['MPI-ESM1-2-HR'],
    #     experiment__short_name__in=['hist-1950'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['MPI-ESM1-2-HR', 'MPI-ESM1-2-XR'],
    #     experiment__short_name__in=['hist-1950', 'control-1950'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).exclude(
    #     climate_model__short_name='MPI-ESM1-2-HR',
    #     experiment__short_name='hist-1950'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['ECMWF-IFS-LR', 'ECMWF-IFS-HR'],
    #     experiment__short_name='spinup-1950',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #    climate_model__short_name='CMCC-CM2-VHR4',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-LL',
    #     experiment__short_name='highres-future',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon', 
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday', 
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-MM',
    #     experiment__short_name='highres-future',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon',
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday',
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-HM',
    #     experiment__short_name='highres-future',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon',
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday',
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).filter(
    #     variable_request__table_name='CFday'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['HadGEM3-GC31-LL', 'HadGEM3-GC31-MM'],
    #     experiment__short_name='spinup-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon',
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday',
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-MH',
    #     experiment__short_name='spinup-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=[
    #         '3hr', '6hrPlev', '6hrPlevPt', 'AERday', 'AERmon', 'Amon',
    #         'CF3hr', 'CFday', 'CFmon', 'E1hr', 'E3hr', 'E3hrPt', 'Eday',
    #         'EdayZ', 'Emon', 'EmonZ', 'Esubhr', 'LImon', 'Lmon', 'day'
    #     ],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='CMCC-CM2-VHR4',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__frequency__in=['6hr'],
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['CMCC-CM2-HR4', 'CMCC-CM2-VHR4'],
    #     experiment__short_name='highresSST-future',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__in=['HadGEM3-GC31-LL', 'HadGEM3-GC31-MM', 'HadGEM3-GC31-HM'],
    #     experiment__short_name='highres-future',
    #     # rip_code__in=[f'r1i{i}p1f1' for i in range(1, 4)],
    #     variable_request__table_name__in=['Omon', 'Oday'],
    #     datafile__isnull=False
    # ).distinct()
    # data_reqs = DataRequest.objects.filter(
    #     institute__short_name='CNRM-CERFACS',
    #     variable_request__table_name='SImon',
    #     datafile__isnull=False
    # ).exclude(
    #     esgfdataset__status='PUBLISHED'
    # ).exclude(
    #     experiment__short_name__startswith='primWP5'
    # ).distinct()
    data_reqs = DataRequest.objects.filter(
        climate_model__short_name__in=['HadGEM3-GC31-LL', 'HadGEM3-GC31-MM'],
        experiment__short_name='spinup-1950',
        variable_request__table_name__in=['Omon', 'Oday'],
        datafile__isnull=False
    ).distinct()
 
 
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
