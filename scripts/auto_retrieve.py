#!/usr/bin/env python
"""
auto_retrieve.py

This script is designed to run in a persistent screen session and to
periodically restore any data that needs to be restored from either elastic
tape or MASS.
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

from django.template.defaultfilters import filesizeformat
from pdata_app.models import RetrievalRequest, Settings
from pdata_app.utils.common import get_request_size, PAUSE_FILES

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)

ONE_HOUR = 60 * 60
TWO_TEBIBYTES = 2 * 2 ** 40

# The institution_ids that should be retrieved from MASS
MASS_INSTITUTIONS = ['MOHC', 'NERC']

# The top-level directory to write output data to
STREAM1_DIR = Settings.get_solo().current_stream1_dir


def run_retrieve_request(retrieval_id):
    """
    Run retrieve_request.py in a subprocess to fetch the appropriate data
    from tape to disk

    :param int retrieval_id:
    """
    retrieval_request = RetrievalRequest.objects.get(id=retrieval_id)

    if get_request_size(retrieval_request) > TWO_TEBIBYTES:
        logger.warning('Skipping retrieval {} as it is bigger than {}.'.format(
            retrieval_id, filesizeformat(TWO_TEBIBYTES).encode('utf-8')
        ))
        return

    # cmd = ('/home/users/jseddon/primavera/LIVE-prima-dm/scripts/'
    #        'retrieve_request.py -l debug -a {} {}'.format(STREAM1_DIR,
    #                                                       retrieval_id))
    cmd = ('/home/users/jseddon/primavera/LIVE-prima-dm/scripts/'
           'retrieve_request.py -l debug {}'.format(retrieval_id))
    try:
        subprocess.check_output(cmd, shell=True)
    except OSError as exc:
        logger.error('Unable to run command:\n{}\n{}'.format(cmd,
                                                             exc.strerror))
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        logger.error('Retrieval failed: {}\n{}'.format(cmd, exc.output))
    else:
        logger.debug('Retrieved id {}'.format(retrieval_id))


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Automatically perform '
                                                 'PRIMAVERA retrieval '
                                                 'requests.')
    tape_sys = parser.add_mutually_exclusive_group(required=True)
    tape_sys.add_argument("-m", "--mass", help="Restore data from MASS",
                          action='store_true')
    tape_sys.add_argument("-e", "--et", help="Restore data from elastic tape",
                          action='store_true')
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
    logger.debug('Starting auto_retrieve.py')

    while True:
        ret_reqs = (RetrievalRequest.objects.filter(date_complete__isnull=True,
                                                    date_deleted__isnull=True).
                    order_by('date_created'))

        for ret_req in ret_reqs:
            # check for retrievals that are purely elastic tape or pure MASS
            if args.mass:
                # however, if pausing the system jump to the wait
                if os.path.exists(PAUSE_FILES['moose:']):
                    logger.debug('Waiting due to {}'.
                                 format(PAUSE_FILES['moose:']))
                    break
                if (ret_req.data_request.filter
                        (institute__short_name__in=MASS_INSTITUTIONS).count()
                        and not ret_req.data_request.exclude
                        (institute__short_name__in=MASS_INSTITUTIONS).count()):
                    run_retrieve_request(ret_req.id)
            elif args.et:
                # however, if pausing the system jump to the wait
                if os.path.exists(PAUSE_FILES['et:']):
                    logger.debug('Waiting due to {}'.
                                 format(PAUSE_FILES['et:']))
                    break
                if (ret_req.data_request.exclude
                        (institute__short_name__in=MASS_INSTITUTIONS).count()
                        and not ret_req.data_request.filter
                        (institute__short_name__in=MASS_INSTITUTIONS).count()):
                    run_retrieve_request(ret_req.id)
            else:
                raise NotImplementedError('Unknown tape system specified.')

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
    main(cmd_args)
