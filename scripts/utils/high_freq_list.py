#!/usr/bin/env python
"""
high_freq_list.py

This script will generate a summary of the high frequency (daily or higher)
variables that are being generated.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import sys

import django
django.setup()
from pdata_app.models import VariableRequest, DataRequest


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

FILENAME = 'PRIMAVERA_high_freq_vars.csv'

logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='List the high frequency '
                                                 'variables that are being '
                                                 'produced.')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    parser.add_argument('--version', action='version',
        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """Run the script"""
    frequencies = ['day', '6hr', '3hr', '1hr']
    institutes = ['EC-Earth-Consortium', 'ECMWF', 'CMCC', 'MPI-M',
                  'CNRM-CERFACS', 'AWI', 'MOHC']

    with open(FILENAME, 'w') as fh:
        header = 'CMOR Variable name, Table name, Frequency, {}\n'.format(
            ', '.join(institutes))
        fh.write(header)

        for vreq in VariableRequest.objects.filter(
                frequency__in=frequencies).order_by(
                '-frequency', 'cmor_name'):
            op_string = '{}, {}, {}, '.format(vreq.cmor_name, vreq.table_name,
                                              vreq.frequency)
            for inst in institutes:
                dreq = DataRequest.objects.filter(variable_request=vreq,
                                                  institute__short_name=inst)
                op_string += 'Y, ' if dreq else 'N, '

            op_string += '\n'
            fh.write(op_string)




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
