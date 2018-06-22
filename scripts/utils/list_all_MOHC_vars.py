#!/usr/bin/env python
"""
list_all_MOHC_vars.py

This script will generate a summary of the all of the HighResMIP
variables that MOHC are planning on generating.
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

FILENAME = 'PRIMAVERA_HighResMIP_vars.csv'

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
    institute = 'MOHC'

    with open(FILENAME, 'w') as fh:
        header = 'CMOR Variable name, Table name\n'
        fh.write(header)

        for vreq in VariableRequest.objects.exclude(
                table_name__startswith='Prim').order_by('-frequency',
                'table_name', 'cmor_name'):
            op_string = '{}, {}\n'.format(vreq.cmor_name, vreq.table_name)

            dreq = DataRequest.objects.filter(variable_request=vreq,
                                              institute__short_name=institute)
            if dreq:
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
