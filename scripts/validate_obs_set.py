#!/usr/bin/env python
"""
validate_obs_set.py

Capture the metadata from an observations set and add this to the database.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import logging.config
import os
import sys

import django
django.setup()

from pdata_app.utils.validate_obs import ObsSet


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def create_obs_set(args):
    """
    Create a new obs set.

    :param args: argparse namespace
    """
    logger.debug('Creating obs dataset from: {}'.format(args.directory))

    try:
        obs_set = ObsSet.from_dirname(args.directory)
        if args.all:
            obs_set.add_files()
        else:
            obs_set.add_files(only_netcdf=True)

    except ValueError as exc:
        logger.error(exc.message)
        sys.exit(1)

    if os.path.exists(args.jsonfile) and not args.force:
        logger.error('Output JSON file already exists: {}'.
                     format(args.jsonfile))
        sys.exit(1)

    obs_set.to_json(args.jsonfile)

    logger.debug('JSON file written to: {}'.format(args.jsonfile))


def apply_obs_set(args):
    """
    Apply a new obs set from a JSON file to the database.

    :param args: argparse namespace
    """
    logger.debug('Applying obs dataset from: {}'.format(args.json))

    # Load from JSON file
    try:
        obs_set = ObsSet.from_json(args.json)
    except IOError as exc:
        logger.error('{}: {}'.format(exc.strerror, exc.filename))
        sys.exit(1)

    # Convert to Django
    obs_set.to_django_instance()


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Validate observation set')
    parser.add_argument('-l', '--log-level',
                        help='set logging level to one of debug, info, warn '
                             '(the default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))

    subparsers = parser.add_subparsers(help='commands')
    # Create command
    create_parser = subparsers.add_parser('create', help='create JSON file')
    create_parser.add_argument('directory', help="the observation set's "
                                                 "top-level directory")
    create_parser.add_argument('jsonfile', help="the full path of the JSON "
                                                "file to save the set's "
                                                "metadata in.")
    create_parser.add_argument('-f', '--force', action='store_true',
                               help='force the overwrite of the existing JSON '
                                    'file')
    create_parser.add_argument('-a', '--all', action='store_true',
                               help='add metadata for all files, not just '
                                    'netCDF')
    create_parser.set_defaults(func=create_obs_set)

    # Apply command
    apply_parser = subparsers.add_parser('apply', help='apply JSON file to '
                                                       'the database')
    apply_parser.add_argument('json', help='the JSON file containing the '
                                           'observation set to add to the '
                                           'database')
    apply_parser.set_defaults(func=apply_obs_set)

    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    args.func(args)


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    if cmd_args.log_level:
        try:
            log_level = getattr(logging, cmd_args.log_level.upper())
        except AttributeError:
            logger.setLevel(logging.WARNING)
            logger.error('log-level must be one of: debug, info, warn '
                         'or error')
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
