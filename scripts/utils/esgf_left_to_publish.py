#!/usr/bin/env python
"""
esgf_left_to_publish.py

Identify any Stream 1 and Stream 2 data that has yet to be submitted to the
ESGF.
"""
import argparse
import logging.config

import django
django.setup()
from pdata_app.models import DataRequest  # nopep8


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)


def get_stream_1_2():
    """
    Calculate the total volume in bytes of files that need to be published.

    :return: volume in bytes.
    """
    amip_expts = ['highresSST-present', 'highresSST-future']
    coupled_expts = ['spinup-1950', 'hist-1950', 'control-1950',
                     'highres-future']
    stream1_2_expts = amip_expts + coupled_expts

    # MOHC stream 2 is members r1i2p2f1 to r1i15p1f1
    mohc_stream2_members = [f'r1i{init_index}p1f1'
                            for init_index in range(2, 16)]

    stream1_2 = DataRequest.objects.filter(
        experiment__short_name__in=stream1_2_expts,
        datafile__isnull=False
    ).exclude(
        # Exclude MOHC Stream 2
        institute__short_name__in=['MOHC', 'NERC'],
        rip_code__in=mohc_stream2_members,
    ).exclude(
        # Exclude EC-Earth atmosphere levels
        climate_model__short_name__startswith='EC-Earth',
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        # Exclude EC-Earth atmosphere levels
        climate_model__short_name__startswith='EC-Earth',
        variable_request__dimensions__contains='alevel'
    ).distinct()

    mohc_stream2_members = DataRequest.objects.filter(
        institute__short_name__in=['MOHC', 'NERC'],
        experiment__short_name__in=stream1_2_expts,
        rip_code__in=mohc_stream2_members,
        datafile__isnull=False
    ).distinct()

    mohc_stream2_low_freq = mohc_stream2_members.filter(
        variable_request__frequency__in=['mon', 'day']
    ).exclude(
        variable_request__table_name='CFday'
    ).distinct()

    mohc_stream2_cfday = mohc_stream2_members.filter(
        variable_request__table_name='CFday',
        variable_request__cmor_name='ps'
    ).distinct()

    mohc_stream2_6hr = mohc_stream2_members.filter(
        variable_request__table_name='Prim6hr',
        variable_request__cmor_name='wsgmax'
    ).distinct()

    mohc_stream2_3hr = mohc_stream2_members.filter(
        variable_request__table_name__in=['3hr', 'E3hr', 'E3hrPt', 'Prim3hr',
                                          'Prim3hrPt'],
        variable_request__cmor_name__in=['rsdsdiff', 'rsds', 'tas', 'uas',
                                         'vas', 'ua50m', 'va50m', 'ua100m',
                                         'va100m', 'ua7h', 'va7h', 'sfcWind',
                                         'sfcWindmax', 'pr', 'psl', 'zg7h']
    ).distinct()

    publishable_files = (stream1_2 | mohc_stream2_low_freq |
                         mohc_stream2_cfday | mohc_stream2_6hr |
                         mohc_stream2_3hr)

    return publishable_files


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Find datasets that have not '
                                                 'been published to the ESGF.')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main():
    """Run the script"""
    stream_1_2 = get_stream_1_2()

    no_esgf = stream_1_2.filter(esgfdataset__isnull=True)

    logger.info('Writing no_esgf_dataset.txt')
    with open('no_esgf_dataset.txt', 'w') as fh:
        for dreq in no_esgf.order_by('project', 'institute', 'climate_model',
                                     'experiment', 'rip_code',
                                     'variable_request__table_name',
                                     'variable_request__cmor_name'):
            fh.write(str(dreq) + '\n')

    remaining = stream_1_2.exclude(esgfdataset__isnull=True)
    not_published = remaining.exclude(esgfdataset__status='PUBLISHED')

    logger.info('Writing status_not_published.txt')
    with open('status_not_published.txt', 'w') as fh:
        for dreq in not_published.order_by('project', 'institute',
                                           'climate_model', 'experiment',
                                           'rip_code',
                                           'variable_request__table_name',
                                           'variable_request__cmor_name'):
            fh.write(str(dreq) + '\n')

    # TODO what about WP5?


if __name__ == "__main__":
    cmd_args = parse_args()

    # configure the logger
    log_level = getattr(logging, cmd_args.log_level.upper())
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
