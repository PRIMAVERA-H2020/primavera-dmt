#!/usr/bin/env python
"""
prim_specific_volumes.py

Calculate the volumes required to store the PRIMAVERA specific additional
variables in the format required by the CREPP system.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import sys

import django
from django.db.models import Sum
django.setup()
from pdata_app.models import DataRequest


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Write to file the volume of '
                                                 'PRIMAVERA specific data.')
    parser.add_argument('filepath', help='the file path to write to')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """Run the script"""
    model_order = [
        'AWI-CM-1-1-LR',
        'AWI-CM-1-1-HR',
        'CMCC-CM2-HR4',
        'CMCC-CM2-VHR4',
        'CNRM-CM6-1',
        'CNRM-CM6-1-HR',
        'EC-Earth3',
        'EC-Earth3P',
        'EC-Earth3-HR',
        'EC-Earth3P-HR',
        'ECMWF-IFS-LR',
        'ECMWF-IFS-MR',
        'ECMWF-IFS-HR',
        'HadGEM3-GC31-LL',
        'HadGEM3-GC31-LM',
        'HadGEM3-GC31-MM',
        'HadGEM3-GC31-MH',
        'HadGEM3-GC31-HM',
        'HadGEM3-GC31-HH',
        'MPIESM-1-2-HR',
        'MPI-ESM1-2-HR',
        'MPIESM-1-2-XR',
        'MPI-ESM1-2-XR'
    ]

    experiment_order = [
        'highresSST-present',
        'highresSST-future',
        'spinup-1950',
        'hist-1950',
        'control-1950',
        'highres-future'
    ]

    table_order = [
        'Primmon',
        'PrimmonZ',
        'PrimOmon',
        'Primday',
        'PrimdayPt',
        'PrimOday',
        'PrimSIday',
        'Prim6hr',
        'Prim6hrPt',
        'PrimO6hr',
        'Prim3hr',
        'Prim3hrPt',
        'Prim1hr',
    ]

    reqs = DataRequest.objects.filter(
        datafile__isnull=False,
        variable_request__table_name__startswith='Prim'
    ).exclude(
        experiment__short_name__in=['primWP5-amv-neg', 'primWP5-amv-pos',
                                    'dcppc-amv-neg', 'dcppc-amv-pos', 
                                    'primWP5-coupledseaice']
    )
    uploaded = list(reqs.values_list(
        'climate_model__short_name',
        'experiment__short_name',
        'rip_code',
        'variable_request__table_name'
    ).distinct())

    uploaded.sort(key=lambda k: (model_order.index(k[0]),
                                 experiment_order.index(k[1]),
                                 k[2],
                                 table_order.index(k[3])))

    with open(args.filepath, 'w') as fh:
        for upload in uploaded:
            data_reqs = DataRequest.objects.filter(
                climate_model__short_name=upload[0],
                experiment__short_name=upload[1],
                rip_code=upload[2],
                variable_request__table_name=upload[3],
                datafile__isnull=False
            )
            total_volume = 0
            for dr in data_reqs.distinct():
                total_volume += (dr.datafile_set.aggregate(Sum('size'))
                                 ['size__sum'])
                total_volume *= 1.1  # Add a fudge factor of 10%
                total_volume /= 1024**4  # Convert bytes to tebibytes
            if upload[0].startswith('HadGEM'):
                institute = '*'
            else:
                institute = data_reqs.first().institute.short_name
            fh.write(f'PRIMAVERA/HighResMIP/{institute}/{upload[0]}/'
                     f'{upload[1]}/{upload[2]}/{upload[3]} '
                     f'{total_volume:.10f}\n')


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
