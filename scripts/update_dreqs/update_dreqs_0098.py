#!/usr/bin/env python
"""
update_dreqs_0098.py

This file removes the files from submission
/group_workspaces/jasmin2/primavera2/upload/CMCC/CMCC-HR4/20180601

which is the CMCC-HR4 control-1950 ocean variables with a version number of
v20180509.
"""
import argparse
import logging.config
import os
import sys

from cf_units import date2num, CALENDAR_GREGORIAN

import django
django.setup()
from pdata_app.utils.replace_file import replace_files
from pdata_app.models import DataSubmission
from pdata_app.utils.common import delete_drs_dir

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def delete_files(query_set):
    """
    Delete any files online from the specified queryset
    """
    directories_found = []
    for df in query_set:
        if df.online:
            try:
                os.remove(os.path.join(df.directory, df.name))
            except OSError as exc:
                logger.error(str(exc))
                sys.exit(1)
            else:
                if df.directory not in directories_found:
                    directories_found.append(df.directory)
            df.online = False
            df.directory = None
            df.save()

    for directory in directories_found:
        if not os.listdir(directory):
            delete_drs_dir(directory)
    logger.debug('{} directories removed'.format(len(directories_found)))


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
    ocean_files = DataSubmission.objects.get(incoming_directory=
        '/group_workspaces/jasmin2/primavera2/upload/CMCC/CMCC-HR4/20180601'
    )
    if ocean_files.datafile_set.count() != 4646:
        logger.error('{} files found, expecting 4646'.format(
            ocean_files.datafile_set.count()))
        sys.exit(1)

    delete_files(ocean_files)
    replace_files(ocean_files.datafile_set.all())


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
