#!/usr/bin/env python
"""
update_dreqs_0329.py

Update the version in the HadGEM3-GC31-HH seaice data.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import DataRequest, Settings  # nopep8
from pdata_app.utils.common import construct_drs_path, delete_drs_dir, get_gws  # nopep8

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir

# The version string to change to
NEW_VERSION_STRING = 'v20210416'


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


def main():
    """
    Main entry point
    """
    dreqs = DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-HH',
        experiment__short_name__in=['control-1950', 'hist-1950',
                                    'highres-future'],
        variable_request__table_name__in=['SImon', 'SIday', 'PrimSIday'],
        datafile__isnull=False
    ).distinct().order_by(
        'experiment__short_name',
        'variable_request__table_name',
        'variable_request__cmor_name'
    )

    num_dreqs = dreqs.count()
    logger.info(f'{num_dreqs} data requests found')

    for dreq in dreqs:
        logger.info(str(dreq))
        old_drs_path = construct_drs_path(dreq.datafile_set.first())
        dreq.datafile_set.update(version=NEW_VERSION_STRING)
        for df in dreq.datafile_set.order_by('name'):
            if not df.online:
                logger.error(f'File not online {df.name}')
                continue
            old_dir = df.directory
            old_path = os.path.join(old_dir, df.name)
            if not os.path.exists(old_path):
                logger.error(f'File not found {old_path}')
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

            # Update symbolic links on primavera5
            if not get_gws(df.directory) == BASE_OUTPUT_DIR:
                old_link_dir = os.path.join(BASE_OUTPUT_DIR,
                                            old_drs_path)
                old_link_path = os.path.join(old_link_dir, df.name)
                if not os.path.exists(old_link_path):
                    logger.error(f'Link not found {old_link_path}')
                    continue
                if not os.path.islink(old_link_path):
                    logger.error(f'Not sym link {old_link_path}')
                    continue
                os.remove(old_link_path)

                new_link_dir = os.path.join(BASE_OUTPUT_DIR,
                                            construct_drs_path(df))
                new_link_path = os.path.join(new_link_dir, df.name)
                if not os.path.exists(new_link_dir):
                    os.makedirs(new_link_dir)
                os.symlink(os.path.join(new_dir, df.name),
                           new_link_path)

                if not os.listdir(old_link_dir):
                    delete_drs_dir(old_link_dir)


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
    main()
