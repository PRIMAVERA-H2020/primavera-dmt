#!/usr/bin/env python2.7
"""
update_dreqs_0058.py

Add an extra file to the EN4 obs set
"""
import argparse
import logging.config
import sys


import django
django.setup()
from django.contrib.auth.models import User

from pdata_app.models import ObservationDataset, ObservationFile


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    obs_set = ObservationDataset.objects.get(name='EN4')

    obs_file_args = {
        "units": "PSU",
        "name": "so_Omon_EN411g_190000-194912.nc",
        "long_name": "Sea Water Salinity",
        "var_name": None,
        "tape_url": None,
        "time_units": "days since 1900-01-01",
        "checksum_value": "f7ba68e5699e886889c36d5fb220051f4f28f78381f61a07d635b5412a9269a9",
        "standard_name": "sea_water_salinity",
        "frequency": "mon",
        "end_time": 18247.28125,
        "incoming_directory": "/group_workspaces/jasmin2/primavera1/cache/jseddon/obs_en4",
        "online": True,
        "directory": "/group_workspaces/jasmin2/primavera1/cache/jseddon/obs_en4",
        "checksum_type": "SHA256",
        "calendar": "standard",
        "start_time": 15.21875,
        "size": 12555659316,
        "obs_set": obs_set
    }

    obs_file = ObservationFile.objects.create(**obs_file_args)


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
