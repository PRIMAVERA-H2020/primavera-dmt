#!/usr/bin/env python2.7
"""
update_dreqs_0030.py

This file adds data and variable requests for CERFACS for both models for all the
experiments.
"""
import argparse
from datetime import datetime
import logging.config
import sys

from cf_units import date2num, CALENDAR_GREGORIAN

import django
django.setup()

from pdata_app.models import (DataRequest, VariableRequest, Experiment,
                              Institute, ClimateModel, Project, Settings)
from pdata_app.utils.dbapi import match_one, get_or_create


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
    new_vreqs = [
        {'table_name': 'AERmon',
         'long_name': 'Surface Albedo',
         'units': '1',
         'var_name': 'albsrfc',
         'standard_name': 'surface_albedo',
         'cell_methods': 'area: time: mean',
         'positive': '',
         'variable_type': 'real',
         'dimensions': 'longitude latitude time',
         'cmor_name': 'albsrfc',
         'modeling_realm': 'aerosol',
         'frequency': 'mon',
         'cell_measures': 'area: areacella',
         'uid': '0fac71f0-817d-11e6-b80b-5404a60d96b5'},
    ]

    new_dreqs = [
        'cltc_AERmon',
        'albsrfc_AERmon'
    ]

    institute_details = {
        'id': 'CNRM-CERFACS',
        'model_ids': ['CNRM-CM6-1-HR', 'CNRM-CM6-1'],
        'calendar': CALENDAR_GREGORIAN
    }

    experiments = {
        'control-1950': {'start_date': datetime(1950, 1, 1),
                         'end_date': datetime(2050, 1, 1)},
        'highres-future': {'start_date': datetime(2015, 1, 1),
                           'end_date': datetime(2051, 1, 1)},
        'hist-1950': {'start_date': datetime(1950, 1, 1),
                      'end_date': datetime(2015, 1, 1)},
        'highresSST-present': {'start_date': datetime(1950, 1, 1),
                               'end_date': datetime(2015, 1, 1)},
        'highresSST-future': {'start_date': datetime(2015, 1, 1),
                              'end_date': datetime(2051, 1, 1)},
        'highresSST-LAI': {'start_date': datetime(1950, 1, 1),
                           'end_date': datetime(2015, 1, 1)},
        'highresSST-smoothed': {'start_date': datetime(1950, 1, 1),
                                'end_date': datetime(2015, 1, 1)},
        'highresSST-p4K': {'start_date': datetime(1950, 1, 1),
                           'end_date': datetime(2015, 1, 1)},
        'highresSST-4co2': {'start_date': datetime(1950, 1, 1),
                            'end_date': datetime(2015, 1, 1)},
        'spinup-1950': {'start_date': datetime(1950, 1, 1),
                        'end_date': datetime(1980, 1, 1)},
    }

    # Experiment
    experiment_objs = []
    for expt in experiments:
        expt_obj = match_one(Experiment, short_name=expt)
        if expt_obj:
            experiment_objs.append(expt_obj)
        else:
            msg = 'experiment {} not found in the database.'.format(expt)
            print msg
            raise ValueError(msg)

    # Institute
    result = match_one(Institute, short_name=institute_details['id'])
    if result:
        institute = result
    else:
        msg = 'institute_id {} not found in the database.'.format(
            institute_details['id']
        )
        print msg
        raise ValueError(msg)

    # Look up the ClimateModel object for each institute_id  and save the
    # results to a dictionary for quick look up later
    model_objs = []
    for clim_model in institute_details['model_ids']:
        result = match_one(ClimateModel, short_name=clim_model)
        if result:
            model_objs.append(result)
        else:
            msg = ('climate_model {} not found in the database.'.
                   format(clim_model))
            print msg
            raise ValueError(msg)

    # The standard reference time
    std_units = Settings.get_solo().standard_time_units

    # create the additional variable requests
    for new_vreq in new_vreqs:
        _vr = get_or_create(VariableRequest, **new_vreq)

    # create the new data requests
    for new_dreq in new_dreqs:
        cmor_name, table_name = new_dreq.split('_')
        if table_name.startswith('Prim'):
            project = match_one(Project, short_name='PRIMAVERA')
        else:
            project = match_one(Project, short_name='CMIP6')

        var_req_obj = match_one(VariableRequest, cmor_name=cmor_name,
                                table_name=table_name)
        if var_req_obj:
            for expt in experiment_objs:
                for clim_model in model_objs:
                    _dr = get_or_create(
                        DataRequest,
                        project=project,
                        institute=institute,
                        climate_model=clim_model,
                        experiment=expt,
                        variable_request=var_req_obj,
                        request_start_time=date2num(
                            experiments[expt.short_name]['start_date'],
                            std_units, institute_details['calendar']
                        ),
                        request_end_time=date2num(
                            experiments[expt.short_name]['end_date'],
                            std_units, institute_details['calendar']
                        ),
                        time_units=std_units,
                        calendar=institute_details['calendar']
                    )
        else:
            msg = ('Unable to find variable request matching '
                   'cmor_name {} and table_name {} in the '
                   'database.'.format(cmor_name, table_name))
            print msg
            raise ValueError(msg)


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
