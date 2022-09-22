#!/usr/bin/env python
"""
make_rose_task_names_ec_earth_prim.py

This script is used to generate a JSON list of the task names that
should be run by the rose suite that performs submissions to the CREPP
system.

All task names are added to the specified JSON file, e.g. `filename.json`, but
an additional file called `filename_name.json` is created containing the task
names that have been added to the JSON file. Any existing `filename_new.json`
file is renamed to `filename_new.json.YYmmddHHMM`.
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

    <climate-model>_<experiment>_<variant-label>_<table>_<variable>

    e.g.:

    HadGEM3-GC31-LM_highresSST-present_r1i1p1f1_Amon_psl
    """
    existing_tasks = []
    if os.path.exists(args.json_file):
        with open(args.json_file) as fh:
            existing_tasks = json.load(fh)

        logger.debug('{} existing tasks loaded from file'.
                     format(len(existing_tasks)))

    highres_future_r1p2 = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        experiment__short_name='highres-future',
        rip_code='r1i1p2f1',
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    highres_future_r2p2 = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        # climate_model__short_name='EC-Earth3P-HR',
        experiment__short_name='highres-future',
        rip_code='r2i1p2f1',
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    highres_future_r3p2 = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        experiment__short_name='highres-future',
        rip_code='r3i1p2f1',
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    amip_future = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        experiment__short_name='highresSST-future',
        rip_code__in=['r1i1p1f1', 'r2i1p1f1', 'r3i1p1f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    amip_past_lr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P',
        experiment__short_name='highresSST-present',
        rip_code__in=['r2i1p1f1', 'r3i1p1f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    amip_past_hr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P-HR',
        experiment__short_name='highresSST-present',
        rip_code__in=['r2i1p1f1', 'r3i1p1f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    hist_lr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P',
        experiment__short_name='hist-1950',
        rip_code__in=['r1i1p2f1', 'r2i1p2f1', 'r3i1p2f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    hist_hr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P-HR',
        experiment__short_name='hist-1950',
        rip_code__in=['r1i1p2f1', 'r2i1p2f1', 'r3i1p2f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    ctrl_lr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P',
        experiment__short_name='control-1950',
        rip_code__in=['r1i1p2f1', 'r2i1p2f1', 'r3i1p2f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    ctrl_hr = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P-HR',
        experiment__short_name='control-1950',
        rip_code__in=['r1i1p2f1', 'r2i1p2f1', 'r3i1p2f1'],
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    amip_r1 = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name__in=['EC-Earth3P', 'EC-Earth3P-HR'],
        experiment__short_name='highresSST-present',
        rip_code='r1i1p1f1',
        variable_request__table_name__startswith='Prim',
        datafile__isnull=False
    ).distinct()

    upwelling_flux = DataRequest.objects.filter(
        climate_model__short_name__contains='EC-Earth3P',
        experiment__short_name='highresSST-present',
        rip_code='r1i1p1f1',
        variable_request__cmor_name__regex='r[ls]u[ts]*',
        datafile__isnull=False
    ).distinct()

    fx = DataRequest.objects.filter(
        climate_model__short_name__contains='EC-Earth3P',
        variable_request__table_name__contains='fx',
        datafile__isnull=False
    ).distinct()

    spinup_lr_all = DataRequest.objects.filter(
        institute__short_name='EC-Earth-Consortium',
        climate_model__short_name='EC-Earth3P',
        experiment__short_name='spinup-1950',
        rip_code='r1i1p2f1',
        datafile__isnull=False
    ).exclude(
        variable_request__dimensions__contains='alevhalf'
    ).exclude(
        variable_request__dimensions__contains='alevel'
    ).distinct()

    # task querysets can be ORed together with |

    all_tasks = (highres_future_r1p2 | highres_future_r2p2 | highres_future_r3p2 | amip_future |
                 amip_past_lr | amip_past_hr | hist_lr | hist_hr | ctrl_lr | ctrl_hr | 
                 upwelling_flux | amip_r1 | fx | spinup_lr_all)

    task_name_list = [
        '{}_{}_{}_{}_{}'.format(dr.climate_model.short_name,
                                dr.experiment.short_name,
                                dr.rip_code,
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
