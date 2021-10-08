#!/usr/bin/env python
"""
update_dreqs_0236.py

Identify gaps in the files for a hard coded experiment
"""
import argparse
import logging.config
import sys

import cf_units

import django
django.setup()
from pdata_app.models import DataRequest

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def identify_gaps_in_files(data_req):
    """
    Check the files in the data request to see if there
    appears to be any files missing from this dataset.
    """
    one_day = 1.
    data_files = data_req.datafile_set.order_by('name')
    gap_found = False
    msg = ''
    for index, data_file in enumerate(data_files):
        if index == 0:
            continue
        start_time = cf_units.num2date(data_file.start_time,
                                       data_file.time_units,
                                       data_file.calendar)
        previous_end_time = cf_units.num2date(data_files[index - 1].end_time,
                                              data_files[index - 1].time_units,
                                              data_files[index - 1].calendar)
        difference = start_time - previous_end_time
        if difference.days > one_day:
            gap_found = True
            msg = f'{difference.days} day gap prior to {data_file.name}'
        else:
            # End of gap so report if there was a gap
            if gap_found:
                print(msg)
                gap_found = False

    if gap_found:
        # Gap extends to the end of files so report last message
        print(msg)


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
    data_reqs = DataRequest.objects.filter(
        climate_model__short_name='EC-Earth3P-HR',
        experiment__short_name='hist-1950',
        rip_code='r1i1p1f1'
    ).order_by(
        'variable_request__table_name',
        'variable_request__cmor_name'
    )

    for data_req in data_reqs:
        identify_gaps_in_files(data_req)


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
