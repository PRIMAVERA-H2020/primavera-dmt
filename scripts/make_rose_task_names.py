#!/usr/bin/env python2.7
"""
make_rose_task_names.py

This script is used to generate a JSON list of the task names that
should be run by the rose suite that performs submissions to the CREPP
system.
"""
import argparse
import datetime
import json
import logging.config
import os
import sys

import django
django.setup()

from pdata_app.models import DataRequest

__version__ = '0.1.0b'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate a JSON list of the Rose task names that should '
                    'be submitted to CREPP.'
    )
    parser.add_argument('json_file', help="the path to the JSON file to "
                                          "generate")
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point

    Task names in the output JSON file are in the form:

    <climate_model>_<experiment>_<table>_<variable>

    e.g.:

    HadGEM3-GC31-LM_highresSST-present_Amon_psl
    """
    existing_tasks = []
    if os.path.exists(args.json_file):
        with open(args.json_file) as fh:
            existing_tasks = json.load(fh)

        logger.debug('{} existing tasks loaded from file'.
                     format(len(existing_tasks)))

    hadgem3_gc31_lm_amip_amon = DataRequest.objects.filter(
        climate_model__short_name='HadGEM3-GC31-MM',
        experiment__short_name='highresSST-present',
        variable_request__table_name='Amon',
        datafile__isnull=False
    ).distinct()

    all_tasks = hadgem3_gc31_lm_amip_amon
    task_name_list = [
        '{}_{}_{}_{}'.format(dr.climate_model.short_name,
                             dr.experiment.short_name,
                             dr.variable_request.table_name,
                             dr.variable_request.cmor_name)
        for dr in all_tasks
    ]
    logger.debug('{} tasks in total'.format(len(all_tasks)))

    with open(args.json_file, 'w') as fh:
        json.dump(task_name_list, fh, indent=4)

    if existing_tasks:
        new_tasks_list = list(set(task_name_list) - set(existing_tasks))

        new_tasks_file = args.json_file.replace('.json', '_new.json')
        if os.path.exists(new_tasks_file):
            suffix = datetime.datetime.utcnow().strftime('%Y%m%d%H%M')
            os.rename(new_tasks_file, new_tasks_file + '.' + suffix)
        with open(new_tasks_file, 'w') as fh:
            json.dump(new_tasks_list, fh, indent=4)
        logger.debug('{} new tasks'.format(len(new_tasks_list)))


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