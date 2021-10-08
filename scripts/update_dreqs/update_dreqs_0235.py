#!/usr/bin/env python
"""
update_dreqs_0235.py

Create new submissions for EC-Earth3P-HR highres-future r1i1p2f1 in
s2hh-future-1 and s2hh-future-2 that were affected by a varying reference time.
"""
import argparse
import logging.config
import sys

import django
django.setup()
from pdata_app.models import DataSubmission
from django.contrib.auth.models import User

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
    # Example incoming_directory:
    # /gws/nopw/j04/primavera4/upload/EC-Earth-Consortium/EC-Earth-3-HR/
    # incoming/s2hh-future-1/CMIP6/3hr
    # Desired output:
    # /gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/
    # batch01/CMIP6/3hr
    dir_paths = [
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/3hr',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlev',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/hus',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/huss',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/mrsos',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/psl',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/sfcWind',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/snw',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/ta',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/tas',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/ts',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/tsl',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/ua',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/uas',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/va',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/vas',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/vortmean',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch01/CMIP6/6hrPlevPt/zg',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/AERmon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/Amon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/cl',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/cli',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/clivi',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/clw',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/clwvi',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/hur',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/hus',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/pfull',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/ps',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rldscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rlutcs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rsdscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rsdt',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rsuscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rsut',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/rsutcs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/ta',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/ta700',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/ua',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/va',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/wap',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/wap500',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch02/CMIP6/CFday/zg',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/day',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/E3hr',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/Eday',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/Emon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/LImon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/CMIP6/Lmon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/Prim3hr',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/Prim6hr',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/Prim6hrPt',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/Primday',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/PrimdayPt',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-1/batch03/PRIMAVERA/Primmon',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/3hr',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlev',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/hus',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/mrsos',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/huss',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/psl',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/sfcWind',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/snw',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/ta',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/tas',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/ts',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/tsl',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/ua',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/uas',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/va',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/vas',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/vortmean',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch04/CMIP6/6hrPlevPt/zg',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/AERmon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/Amon',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/cl',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/cli',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/clivi',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/clw',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/clwvi',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/hur',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/hus',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/pfull',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/ps',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rldscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rlutcs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rsdscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rsdt',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rsuscs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rsut',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/rsutcs',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/ta',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/ta700',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/ua',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/va',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/wap',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/wap500',
        # '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch05/CMIP6/CFday/zg',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/day',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/E3hr',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/Eday',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/Emon',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/LImon',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/CMIP6/Lmon',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/Prim3hr',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/Prim6hr',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/Prim6hrPt',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/Primday',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/PrimdayPt',
        '/gws/nopw/j04/primavera1/upload/EC-Earth-Consortium/s2hh-future-2/batch06/PRIMAVERA/Primmon'
    ]

    gijs = User.objects.get(username='gvdoord')

    for dir_path in dir_paths:
        ds = DataSubmission.objects.create(
            incoming_directory=dir_path,
            directory=dir_path,
            user=gijs,
            status='PENDING_PROCESSING'
        )


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
