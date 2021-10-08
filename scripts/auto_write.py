#!/usr/bin/env python
"""
auto_write.py

This script is designed to run in a persistent screen session and to
periodically write any validated submissions to elastic tape.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import datetime
import logging.config
import os
import subprocess
import sys
from time import sleep

import django
django.setup()
from django.db.models import Count

from pdata_app.models import DataSubmission
from pdata_app.utils.common import PAUSE_FILES

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

ONE_HOUR = 15 * 60


def run_write(data_sub):
    """
    Run submissions_to_tape.py in a subprocess to write the appropriate data
    to tape from disk

    :param pdata_app.models.DataSubmission data_sub: The submission to write.
    """
    if data_sub.online_status() != 'online':
        logger.warning("Skipping {} because it's status is {}.".
                       format(data_sub, data_sub.online_status()))
        return

    logger.debug('Auto-writing {}'.format(data_sub))

    cmd = [
        sys.executable,
        os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     'submissions_to_tape.py')),
        '-l',
        'debug',
        data_sub.incoming_directory
    ]

    cmd_out = subprocess.run(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

    if cmd_out.returncode:
        logger.error('Command failed\n{}\n{}\n{}'.
                     format(' '.join(cmd), cmd_out.stdout.decode('utf-8'),
                            cmd_out.stderr.decode('utf-8')))


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Automatically perform '
                                                 'PRIMAVERA tape writes.')
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
    logger.debug('Starting auto_write.py')

    while True:
        if os.path.exists(PAUSE_FILES['et:']):
            logger.debug('Waiting due to {}'.format(PAUSE_FILES['et:']))
        else:
            data_subs = (DataSubmission.objects.
                         annotate(Count('datafile__tape_url')).
                         annotate(Count('datafile')).
                         filter(datafile__tape_url__count=0,
                                status='VALIDATED',
                                datafile__count__gt=0))

            for ds in data_subs:
                run_write(ds)

        logger.debug('Waiting for one hour at {}'.format(
            datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        sleep(ONE_HOUR)


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
