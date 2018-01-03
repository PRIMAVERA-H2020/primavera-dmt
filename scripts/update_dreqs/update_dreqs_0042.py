#!/usr/bin/env python2.7
"""
update_dreqs_0042.py

This script removes all submitted files for the high and low resolution AMIP
runs for the following variables:

'hfss_day',
'evspsbl_Amon',
'evspsbl_Prim3hr',
'evspsbl_Primday',
'hfls_day',
'hfss_Amon',
'hfss_3hr',
'tso_3hr',
'hfls_Amon',
'hfls_3hr'

"""
import argparse
import logging.config
import os
import sys

from cf_units import date2num, CALENDAR_GREGORIAN

import django
django.setup()
from pdata_app.utils.replace_file import replace_file
from pdata_app.models import DataFile, ReplacedFile
from pdata_app.utils.common import delete_drs_dir

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


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
    var_tables = [
        'evspsbl_Amon',
        'evspsbl_Primday',
        'evspsbl_Prim3hr',
        'hfls_Amon',
        'hfls_day',
        'hfls_3hr',
        'hfss_Amon',
        'hfss_day',
        'hfss_3hr',
        'tso_3hr',
    ]
    models = ['EC-Earth3-HR', 'EC-Earth3']
    experiment = 'highresSST-present'

    for var_table in var_tables:
        var, __, table = var_table.partition('_')
        for model in models:
            query_set = DataFile.objects.filter(
                data_request__climate_model__short_name=model,
                data_request__experiment__short_name=experiment,
                variable_request__table_name=table,
                variable_request__cmor_name=var
            )
            logger.debug('{} {} {} {}'.format(model, table, var,
                                              query_set.count()))

            directories_found = []
            for df in query_set:
                if df.online:
                    try:
                        os.remove(os.path.join(df.directory, df.name))
                    except OSError as exc:
                        logger.error(str(exc))
                        sys.exit(1)
                    else:
                        if df.directory not in directories_found:
                            directories_found.append(df.directory)
                    df.online = False
                    df.directory = None
                    df.save()

            for directory in directories_found:
                if not os.listdir(directory):
                    delete_drs_dir(directory)

            replace_file(query_set)


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
