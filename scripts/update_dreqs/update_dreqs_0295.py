#!/usr/bin/env python
"""
update_dreqs_0295.py

Update the version in the CMMC-CM2-VHR4 control-1950 data.
"""
import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()
from pdata_app.models import DataRequest, Settings # nopep8
from pdata_app.utils.common import construct_drs_path, delete_drs_dir, get_gws  # nopep8

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir

def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Add additional data requests')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    dreqs = DataRequest.objects.filter(
        climate_model__short_name='CMCC-CM2-VHR4',
        experiment__short_name='control-1950',
        datafile__isnull=False
    ).distinct().order_by(
        'variable_request__table_name', 'variable_request__cmor_name'
    )

    num_dreqs = dreqs.count()
    logger.info(f'{num_dreqs} data requests found')

    for dreq in dreqs:
        dreq.datafile_set.update(version='v20200917')
        for df in dreq.datafile_set.filter(online=True).order_by('name'):
            old_dir = df.directory
            old_path = os.path.join(old_dir, df.name)
            if not os.path.exists(old_path):
                logger.error(f'{old_path} not found')
                continue
            new_dir = os.path.join(get_gws(df.directory),
                                   construct_drs_path(df))
            if df.directory != new_dir:
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)

                os.rename(old_path,
                          os.path.join(new_dir, df.name))
                df.directory = new_dir
                df.save()

            # Delete original dir if it's now empty
            if not os.listdir(old_dir):
                delete_drs_dir(old_dir)


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
