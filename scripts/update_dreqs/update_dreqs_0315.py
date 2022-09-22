#!/usr/bin/env python
"""
update_dreqs_0315.py

Copy of make_esgf_json.py to just add MPI-ESM1-2-XR highresSST-present
PRIMAVERA specific data requests into pre-proc.
"""
import argparse
import json
import logging.config
import sys

import django
django.setup()

from pdata_app.models import (Institute, ClimateModel, Experiment, DataRequest)

__version__ = '0.1.0b'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def make_dict():
    """
    Make a dictionary of the objects that are required for the post-processing.

    :returns: A dictionary of the required objects.
    :rtype: dict
    """
    return {
        'source_id': [],
        'experiment_id': [],
        'institution_id': [],
        'data_requests': [
            data_request for data_request in
            DataRequest.objects.filter(
                climate_model__short_name__startswith='CNRM-CM6-1',
                experiment__short_name__startswith='primWP5-amv',
                # rip_code='r1i1p1f1',
                # variable_request__frequency='3hr',
                datafile__isnull=False
            ).distinct()
        ]
    }


def _object_to_default(obj):
    """
    Convert known objects to a form that can be serialized by JSON
    """
    if isinstance(obj, (ClimateModel, Experiment)):
        return {'__class__': obj.__class__.__name__,
                '__module__': obj.__module__,
                '__kwargs__': {'short_name': obj.short_name}}
    if isinstance(obj, Institute):
        return {'__class__': 'Institution',
                '__module__': obj.__module__,
                '__kwargs__': {'short_name': obj.short_name}}
    elif isinstance(obj, DataRequest):
        return {'__class__': obj.__class__.__name__,
                '__module__': obj.__module__,
                '__kwargs__': {'table_id': obj.variable_request.table_name,
                               'cmor_name': obj.variable_request.cmor_name,
                               'institution_id__name':
                                   obj.institute.short_name,
                               'source_id__name': obj.climate_model.short_name,
                               'experiment_id__name': obj.experiment.short_name,
                               'variant_label': obj.rip_code
                               }}
    else:
        msg = 'Unknown type to save to JSON: {}'.format(obj.__class__.__name__)
        raise TypeError(msg)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Make a copy of the data requests in a JSON file for '
                    'loading into the ESGF data fixing software'
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
    """
    required_objs = make_dict()
    with open(args.json_file, 'w') as fh:
        json.dump(required_objs, fh, indent=4, default=_object_to_default)


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
