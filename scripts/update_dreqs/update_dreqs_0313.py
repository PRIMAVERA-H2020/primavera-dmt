#!/usr/bin/env python
"""
update_dreqs_0313.py

Create elastic tape retrievals for corrupted EC-Earth files in the upwelling fix
incoming  directory.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import ReplacedFile

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


AFFECTED_FILES = [
    'rsus_3hr_EC-Earth3P_highresSST-present_r1i1p1f1_gr_200207010000-200207312100.nc',
    'rlutcs_Amon_EC-Earth3P_highresSST-present_r1i1p1f1_gr_197401-197412.nc',
    'rlutcs_Amon_EC-Earth3P_highresSST-present_r1i1p1f1_gr_199801-199812.nc',
    'rsus_Amon_EC-Earth3P_highresSST-present_r1i1p1f1_gr_199801-199812.nc',
    'rlutcs_CFday_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19830201-19830228.nc',
    'rsut_CFday_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19690301-19690331.nc',
    'rsut_CFday_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19880101-19880131.nc',
    'rsut_CFday_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19910501-19910531.nc',
    'rsut_CFday_EC-Earth3P_highresSST-present_r1i1p1f1_gr_20150301-20150331.nc',
    'rsut_E3hr_EC-Earth3P_highresSST-present_r1i1p1f1_gr_200903010000-200903312100.nc',
    'rsutcs_E3hr_EC-Earth3P_highresSST-present_r1i1p1f1_gr_196607010000-196607312100.nc',
    'rsutcs_E3hr_EC-Earth3P_highresSST-present_r1i1p1f1_gr_196810010000-196810312100.nc',
    'rlut_day_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19510501-19510531.nc',
    'rlut_day_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19730701-19730731.nc',
    'rlut_day_EC-Earth3P_highresSST-present_r1i1p1f1_gr_20080401-20080430.nc',
    'rsus_day_EC-Earth3P_highresSST-present_r1i1p1f1_gr_19571001-19571031.nc',
    'rlutcs_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19750201-19750228.nc',
    'rlutcs_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19950301-19950331.nc',
    'rsut_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19750401-19750430.nc',
    'rsut_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19810601-19810630.nc',
    'rsut_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_20120501-20120531.nc',
    'rsutcs_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19670201-19670228.nc',
    'rsutcs_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_20020101-20020131.nc',
    'rsutcs_CFday_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_20111101-20111130.nc',
    'rlus_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19571201-19571231.nc',
    'rlus_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19650801-19650831.nc',
    'rlut_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19660801-19660831.nc',
    'rlut_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_20110201-20110228.nc',
    'rsus_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_19650201-19650228.nc',
    'rsus_day_EC-Earth3P-HR_highresSST-present_r1i1p1f1_gr_20120101-20120131.nc',
]

def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Create retrieval requests')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    data_files = ReplacedFile.objects.filter(name__in=AFFECTED_FILES)

    num_found = data_files.count()
    num_expected = 30
    if num_found != num_expected:
        logger.error(f'{num_found} files found but expecting {num_expected}')
        sys.exit(1)

    tape_ids = data_files.values_list('tape_url', flat=True).distinct()

    for tape_id in tape_ids:
        filename = f'{tape_id.replace(":", "_")}.txt'
        with open(filename, 'w') as fh:
            id_files = data_files.filter(tape_url=tape_id)
            for data_file in id_files:
                tape_path = os.path.join(data_file.incoming_directory,
                                         data_file.name.replace('Earth3P', 'Earth3'))
                fh.write(f'{tape_path}\n')

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
