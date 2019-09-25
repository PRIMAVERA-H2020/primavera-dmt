#!/usr/bin/env python
"""
update_dreqs_0223.py

Identify variables that have a different out_name to cmor_name and save these
to the DMT's VariableRequest table.
"""
import argparse
import json
import logging.config
import os
import sys

import django
django.setup()
from pdata_app.models import VariableRequest

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


MIP_TABLE_DIR = '/home/h04/jseddon/primavera/cmip6-cmor-tables/Tables'


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
    for table_name in (VariableRequest.objects.order_by('table_name').
            values_list('table_name', flat=True).distinct()):
        if not table_name.startswith('Prim'):
            table_file = f'CMIP6_{table_name}.json'
        else:
            table_file = f'PRIMAVERA_{table_name}.json'
        with open(os.path.join(MIP_TABLE_DIR, table_file)) as fh:
            mip_table = json.load(fh)

        for var_req in (VariableRequest.objects.filter(table_name=table_name)
                .order_by('cmor_name')):
            cmor_name = var_req.cmor_name
            try:
                out_name = mip_table['variable_entry'][cmor_name]['out_name']
            except KeyError:
                logger.error(f'No entry found for {cmor_name} in table '
                             f'{table_name}')
                continue
            if not (out_name == cmor_name):
                var_req.out_name = out_name
                var_req.save()
                print(f'{cmor_name}_{table_name} {out_name}')


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
