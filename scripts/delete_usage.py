#!/usr/bin/env python2.7
"""
delete_request.py

This script is run by the admin to delete previously retrieved data from the
file structure.
"""
import argparse
import datetime
from itertools import chain
import logging.config
import os
import sys

import cf_units

import django
django.setup()
from django.db.models.query import QuerySet

from pdata_app.models import RetrievalRequest


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Delete previously restored data files from their current '
                    'location for a specified retrieval request.')
    parser.add_argument('retrieval_id', help='the id of the retrieval request '
        'to carry out.', type=int)
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
    rra = RetrievalRequest.objects.get(id=26)
    rrk = RetrievalRequest.objects.get(id=30)

    # dra = rra.data_request.first()
    # drk = rrk.data_request.first()

    for data_req in rra.data_request.all():
        all_files = data_req.datafile_set.filter(online=True,
                                                 directory__isnull=False)
        time_units = all_files[0].time_units
        calendar = all_files[0].calendar
        start_float = None
        if rra.start_year is not None and time_units and calendar:
            start_float = cf_units.date2num(
                datetime.datetime(rra.start_year, 1, 1), time_units,
                calendar
            )
        end_float = None
        if rra.end_year is not None and time_units and calendar:
            end_float = cf_units.date2num(
                datetime.datetime(rra.end_year + 1, 1, 1), time_units,
                calendar
            )

        timeless_files = all_files.filter(start_time__isnull=True)

        timed_files = (all_files.exclude(start_time__isnull=True).
            filter(start_time__gte=start_float,
                   end_time__lt=end_float))

        files_to_delete = QuerySet.union(timeless_files, timed_files)

        other_retrievals = RetrievalRequest.objects.filter(
            data_request=data_req, data_finished=False
        )
        for ret_req in other_retrievals:
            ret_all_files = data_req.datafile_set.filter(online=True,
                                                     directory__isnull=False)
            time_units = ret_all_files[0].time_units
            calendar = ret_all_files[0].calendar
            ret_start_float = None
            if ret_req.start_year is not None and time_units and calendar:
                ret_start_float = cf_units.date2num(
                    datetime.datetime(ret_req.start_year, 1, 1), time_units,
                    calendar
                )
            ret_end_float = None
            if ret_req.end_year is not None and time_units and calendar:
                ret_end_float = cf_units.date2num(
                    datetime.datetime(ret_req.end_year + 1, 1, 1), time_units,
                    calendar
                )

            ret_timeless_files = ret_all_files.filter(start_time__isnull=True)

            ret_timed_files = (ret_all_files.exclude(start_time__isnull=True).
                filter(start_time__gte=ret_start_float,
                       end_time__lt=ret_end_float))

            files_to_delete = (files_to_delete.difference(ret_timeless_files).
                difference(ret_timed_files))

        logger.debug('** {}'.format(files_to_delete.distinct().count()))


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
