#!/usr/bin/env python
"""
update_dreqs_0332.py

Update the version of the CMCC seaice files and move into the
correct directory if they're online.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import DataRequest, Settings
from pdata_app.utils.common import (construct_drs_path, delete_drs_dir,
                                    get_gws, is_same_gws)

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

NEW_VERSION = 'v20200917'

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


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
    dreqs_hr = DataRequest.objects.filter(
        climate_model__short_name='CMCC-CM2-HR4',
        experiment__short_name__in=['hist-1950', 'control-1950'],
        variable_request__table_name__startswith='SI',
        datafile__isnull=False
    ).distinct()

    dreqs_vhr = DataRequest.objects.filter(
        climate_model__short_name='CMCC-CM2-VHR4',
        experiment__short_name='hist-1950',
        variable_request__table_name__startswith='SI',
        datafile__isnull=False
    ).distinct()

    dreqs = dreqs_hr | dreqs_vhr

    logger.debug(f'Found {dreqs.count()} data requests')

    for dreq in dreqs:
        logger.debug(f'Processing {dreq}')
        old_directories = []
        for df in dreq.datafile_set.order_by('name'):
            if not df.online:
                logger.error(f'Not online {df.name}')
                continue
            if df.version == NEW_VERSION:
                logger.warning(f'Already at {NEW_VERSION} {df.name}')
                continue
            # save the sym link directory before we make any changes
            if not is_same_gws(BASE_OUTPUT_DIR, df.directory):
                old_sym_link_dir = os.path.join(BASE_OUTPUT_DIR,
                                                construct_drs_path(df))
            # now get back to updating the version
            df.version = NEW_VERSION
            gws = get_gws(df.directory)
            new_dir = os.path.join(gws, construct_drs_path(df))
            old_directory = df.directory
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            os.rename(os.path.join(df.directory, df.name),
                      os.path.join(new_dir, df.name))
            df.directory = new_dir
            df.save()
            if old_directory not in old_directories:
                old_directories.append(old_directory)

            # Update any sym links too
            if not is_same_gws(BASE_OUTPUT_DIR, df.directory):
                sym_link_path = os.path.join(old_sym_link_dir, df.name)
                if os.path.lexists(sym_link_path):
                    if os.path.islink(sym_link_path):
                        os.remove(sym_link_path)
                        if old_sym_link_dir not in old_directories:
                            old_directories.append(old_sym_link_dir)
                sym_link_dir = os.path.join(BASE_OUTPUT_DIR,
                                            construct_drs_path(df))
                if not os.path.exists(sym_link_dir):
                    os.makedirs(sym_link_dir)
                sym_link_path = os.path.join(sym_link_dir, df.name)
                os.symlink(os.path.join(df.directory, df.name), sym_link_path)

        for directory in old_directories:
            if not os.listdir(directory):
                delete_drs_dir(directory)
            else:
                logger.error(f'Not empty {directory}')


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
