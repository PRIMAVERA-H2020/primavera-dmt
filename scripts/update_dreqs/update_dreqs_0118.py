#!/usr/bin/env python
"""
update_dreqs_0118.py

To test update_dreqs_0117.py it is necessary to have some test data in a
different directory that has been copied from the main data area.

This script copies the data from its current directory to the test area.

THIS SCRIPT SHOULD NOT BE RUN AGAINST THE LIVE DATABASE!!!
"""
import argparse
import logging.config
import os
import shutil
import sys

import django
django.setup()
import pdata_site
from pdata_app.models import DataRequest
from pdata_app.utils.common import construct_drs_path

__version__ = '0.1.0b'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


TEST_DATA_DIR = '/gws/nopw/j04/primavera3/cache/jseddon/test_stream1'


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Copy some test data and '
                                                 'update its path in the test '
                                                 'database.')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main():
    """Main entry point"""
    data_reqs = DataRequest.objects.filter(
        climate_model__short_name='EC-Earth3',
        experiment__short_name='highresSST-present',
        rip_code__in=['r1i1p1f1'],
        variable_request__table_name='Amon',
        variable_request__cmor_name__in=[
            'clt', 'hus', 'pr', 'rlut', 'rlutcs', 'rsut', 'rsutcs', 'ta', 
            'tas', 'ts', 'ua', 'va', 'zg'
        ]
    )
    logger.debug('{} data requests found'.format(data_reqs.count()))

    for data_req in data_reqs:
        for data_file in data_req.datafile_set.all():
            if not data_file.online:
                raise ValueError('{} is not online'.format(data_file.name))
            src_path = os.path.join(data_file.directory, data_file.name)
            dest_dir = os.path.join(TEST_DATA_DIR,
                                    construct_drs_path(data_file))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            dest_path = os.path.join(dest_dir, data_file.name)
            shutil.copyfile(src_path, dest_path)
            data_file.directory = dest_dir
            data_file.save()


if __name__ == "__main__":
    # check that we're definitely not on the live system
    if (pdata_site.settings.DATABASES['default']['HOST'] ==
            'prima-dm.ceda.ac.uk'):
        raise ValueError('This script must not be run on the live system')
    if pdata_site.settings.DATABASES['default']['HOST'] != '':
        raise ValueError('This script must not be run on the live system')
    if pdata_site.settings.DATABASES['default']['NAME'] != 'pdata_test':
        raise ValueError('This script must not be run on the live system')

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
