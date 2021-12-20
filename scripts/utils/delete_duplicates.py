#!/usr/bin/env python
"""
delete_duplicates.py

Scan the specified file path and for any files found check if they are in the
DMT, and if so delete this copy if they are already in the CEDA archive.
"""
import argparse
import logging.config
from pathlib import Path

import django
django.setup()
from pdata_app.models import DataFile  # nopep8
from pdata_app.utils.common import delete_drs_dir, ilist_files  # nopep8


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Delete duplicates')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('top_path', help='the top level of the path to scan')
    parser.add_argument('-n', '--dryrun', help="don't delete, just report",
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    for path in ilist_files(args.top_path, ignore_symlinks=True):
        data_file = Path(path)
        try:
            django_file = DataFile.objects.get(name=data_file.name)
        except django.core.exceptions.ObjectDoesNotExist:
            logger.debug(f'Not in DMT: {path}')
            continue

        if django_file.directory.startswith('/badc'):
            if not args.dryrun:
                action = 'Deleting'
                data_file.unlink()
                delete_drs_dir(str(data_file.parent))
            else:
                action = 'Deletable'
            logger.debug(f'{action}: {path}')


if __name__ == "__main__":
    cmd_args = parse_args()

    # determine the log level
    log_level = getattr(logging, cmd_args.log_level.upper())

    # configure the logger
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(levelname)s: %(message)s',
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
