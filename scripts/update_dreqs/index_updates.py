#!/usr/bin/env python
"""
index_updates.py

This file adds an issue to any ECMWF-IFS-LR coupled files received so far
describing the coupling issue that was found with them.
"""
from __future__ import unicode_literals, division, absolute_import

import argparse
import glob
import importlib
import logging.config
import os
import sys


__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


HTML_FILE = 'update_dreqs.html'


def _ouput_headers(fh):
    txt = """<html>
<head><title>update_dreqs</title></head>
<body>
<table border="1" cellpadding="10">\n
"""
    fh.write(txt)


def _ouput_footers(fh):
    txt = """
</table>
</body>
</html>
"""
    fh.write(txt)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Index the docstrings of the '
                                                 'update_dreqs_nnnn.py scripts')
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
    update_dir = os.path.dirname(__file__)
    update_files = glob.glob(os.path.join(update_dir, 'update_dreqs_*.py'))
    update_files.sort()

    with open(os.path.join(update_dir, HTML_FILE), 'w') as fh:
        _ouput_headers(fh)
        for update_file in update_files:
            import_string = os.path.basename(update_file.rstrip('.py'))
            doc_string = importlib.import_module(import_string).__doc__
            file_name = os.path.basename(update_file)
            description = '\n'.join(doc_string.split('\n')[2:])
            fh.write('<tr><td>{}</td><td>{}</td></tr>\n'.format(file_name,
                                                                description))
        _ouput_footers(fh)


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
