#!/usr/bin/env python
"""
update_dreqs_0180.py

ESGF AttributeUpdate
Generate the JSON file of DRS ids to pass to Rose suite.
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import argparse
import json
import logging.config
import sys

import django
django.setup()

from pdata_app.models import DataRequest


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

TEST_DATA_DIR = '/gws/nopw/j04/primavera3/cache/jseddon/test_stream1'


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('json_file', help='the name of the JSON file to save '
                                          'the request ids in')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='EC-Earth3P-HR',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'        
    # ).distinct()
    # logger.debug('{} data requests found'.format(old_data_reqs.count()))

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='EC-Earth3P-HR',
    #     experiment__short_name='control-1950',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).exclude(
    #     variable_request__table_name__startswith='Prim'        
    # ).distinct()

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='EC-Earth3P',
    #     experiment__short_name='spinup-1950',
    #     variable_request__table_name__startswith='Prim',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='EC-Earth3-HR',
    #     experiment__short_name='spinup-1950',
    #     variable_request__frequency='mon',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='EC-Earth3P-HR',
    #     experiment__short_name='spinup-1950',
    #     # variable_request__frequency='mon',
    #     # variable_request__frequency='day',
    #     # variable_request__frequency='6hr',
    #     variable_request__frequency='3hr',
    #     rip_code='r1i1p1f1',
    #     datafile__isnull=False
    # ).exclude(
    #     variable_request__dimensions__contains='alevhalf'
    # ).exclude(
    #     variable_request__dimensions__contains='alevel'
    # ).distinct()

    # both = DataRequest.objects.filter(
    #     climate_model__short_name__startswith='CMCC-CM2',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name='6hrPlevPt',
    #     variable_request__cmor_name__in=['hus7h', 'huss', 'psl', 'sfcWind', 
    #                                      'tas', 'ts', 'uas', 'vas'],
    #     datafile__isnull=False
    # ).distinct()
    # hr4 = DataRequest.objects.filter(
    #     climate_model__short_name='CMCC-CM2-HR4',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=['6hrPlev', '6hrPlevPt'],
    #     variable_request__cmor_name__in=['ua7h', 'va7h'],
    #     datafile__isnull=False
    # ).distinct()
    # old_data_reqs = both | hr4

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__startswith='CMCC-CM2',
    #     experiment__short_name='highresSST-present',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name='6hrPlevPt',
    #     variable_request__cmor_name__in=['hus7h', 'huss', 'psl', 'sfcWind',
    #                                      'tas', 'ts', 'uas', 'vas'],
    #     datafile__isnull=False
    # ).distinct()

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name='HadGEM3-GC31-LL',
    #     experiment__short_name='hist-1950',
    #     rip_code='r1i1p1f1',
    #     variable_request__table_name__in=['PrimSIday', 'SIday', 'SImon'],
    #     datafile__isnull=False
    # ).distinct()

    # old_data_reqs = DataRequest.objects.filter(
    #     climate_model__short_name__startswith='HadGEM3-GC31',
    #     variable_request__table_name__in=['PrimSIday', 'SIday', 'SImon'],
    #     datafile__isnull=False
    # ).distinct()

    old_data_reqs = DataRequest.objects.filter(
        institute__short_name='ECMWF',
        experiment__short_name__startswith='primWP5-amv',
        datafile__isnull=False
    ).distinct()

    logger.debug('{} data requests found'.format(old_data_reqs.count()))

    reqs_list = [
        '{}_{}_{}_{}_{}'.format(
            dr.climate_model.short_name,
            dr.experiment.short_name,
            dr.rip_code,
            dr.variable_request.table_name,
            dr.variable_request.cmor_name
        )
        for dr in old_data_reqs.order_by(
            'variable_request__table_name',
            'variable_request__cmor_name'
        )
    ]

    with open(args.json_file, 'w') as fh:
        json.dump(reqs_list, fh, indent=4)


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
