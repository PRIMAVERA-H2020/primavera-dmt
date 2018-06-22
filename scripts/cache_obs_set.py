#!/usr/bin/env python
"""
cache_obs_set.py

For each observation set, cache the foreign key relationships to speed the page
load.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import os
import sys

import django
django.setup()

from django.utils import timezone

from pdata_app.models import ObservationDataset

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Cache observation set')
    parser.add_argument('-l', '--log-level',
                        help='set logging level to one of debug, info, warn '
                             '(the default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))

    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    for obs_set in ObservationDataset.objects.all():
        logger.debug('Caching {}'.format(obs_set))
        if obs_set.variables:
            obs_set.cached_variables = ', '.join(obs_set.variables)
        else:
            obs_set.cached_variables = None

        if obs_set.start_time:
            obs_set.cached_start_time = timezone.make_aware(obs_set.start_time,
                                                            timezone.utc)
        else:
            obs_set.cached_start_time = None
        if obs_set.end_time:
            obs_set.cached_end_time = timezone.make_aware(obs_set.end_time,
                                                          timezone.utc)
        else:
            obs_set.cached_end_time = None

        obs_set.cached_num_files = obs_set.obs_files.count()

        if obs_set.directories:
            obs_set.cached_directories = os.path.normpath(
                os.path.commonprefix(obs_set.directories))

        obs_set.save()


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    if cmd_args.log_level:
        try:
            log_level = getattr(logging, cmd_args.log_level.upper())
        except AttributeError:
            logger.setLevel(logging.WARNING)
            logger.error('log-level must be one of: debug, info, warn '
                         'or error')
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
