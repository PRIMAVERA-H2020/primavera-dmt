#!/usr/bin/env python2.7
"""
submissions_to_tape.py

This script is designed to be run by a cron job, on the cron server at JASMIN.
It identifies all data submissions that don't contain any files that have a
tape url. For each submission identified, the files in the submission are
listed and the `et_put.py` command is called to write these files to elastic
tape. Each file in the submission is updated to include the tape URL in the
elastic tape system.
"""
import argparse
import logging.config
import os
import re
import subprocess
import sys

import django
django.setup()
import django.core.exceptions
from django.db.models import Count
from django.template.defaultfilters import pluralize

from pdata_app.models import DataSubmission
from pdata_app.utils.common import get_temp_filename

from vocabs.vocabs import STATUS_VALUES

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


def _get_submission_object(submission_dir):
    """
    :param str submission_dir: The path of the submission's top level
    directory.
    :returns: The object corresponding to the submission.
    :rtype: pdata_app.models.DataSubmission
    """
    try:
        data_sub = DataSubmission.objects.get(
            incoming_directory=submission_dir)
    except django.core.exceptions.MultipleObjectsReturned:
        msg = 'Multiple DataSubmissions found for directory: {}'.format(
            submission_dir)
        logger.error(msg)
        raise ValueError(msg)
    except django.core.exceptions.ObjectDoesNotExist:
        msg = ('No DataSubmissions have been found in the database for '
               'directory: {}.'.format(submission_dir))
        logger.error(msg)
        raise ValueError(msg)

    return data_sub


def _run_command(command):
    """
    Run the command specified and return any output to stdout or stderr as
    a list of strings.

    :param str command: The complete command to run.
    :returns: Any output from the command as a list of strings.
    :raises RuntimeError: If the command did not complete successfully.
    """
    try:
        cmd_out = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                          shell=True)
    except subprocess.CalledProcessError as exc:
        msg = ('Command did not complete sucessfully.\ncommmand:\n{}\n'
               'produced error:\n{}'.format(command, exc.output))
        logger.warning(msg)
        if exc.returncode != 0:
            raise RuntimeError(msg)

    return cmd_out.rstrip().split('\n')


def submission_to_tape(directory, overwrite=False):
    """
    Main entry point
    """
    logger.debug('Starting submission: {}'.format(directory))

    try:
        data_sub = _get_submission_object(directory)
    except ValueError:
        sys.exit(1)

    if data_sub.get_tape_urls() and not overwrite:
        msg = ('Data submission has already been written to tape. Re-run this '
               'script with the -o, --overwrite option to force it to be '
               'written again.')
        logger.error(msg)
        sys.exit(1)

    # make a file containing the paths of the files to write to tape
    filelist_name = get_temp_filename('filelist.txt')
    with open(filelist_name, 'w') as fh:
        for data_file in data_sub.get_data_files():
            fh.write(os.path.join(data_file.directory, data_file.name) + '\n')
    logger.debug('File list written to {}'.format(filelist_name))

    # run the et_put.py command to send the files to tape
    cmd = 'et_put.py -v -w primavera -f {}'.format(filelist_name)
    cmd_output = _run_command(cmd)

    # find the batch id from the text returned by et_put.py
    batch_id = None
    for line in cmd_output:
        components = re.match(r'Batch ID: (\d+)', line)
        if components:
            batch_id = components.group(1)
            break

    if batch_id:
        logger.debug('Submission written to elastic tape with batch id {}'.
                     format(batch_id))
        # add the batch id to all of the submission's files.
        num_files_updated = 0
        for data_file in data_sub.get_data_files():
            data_file.tape_url = 'et:{}'.format(batch_id)
            data_file.save()
            num_files_updated += 1
        logger.debug('Elastic tape URL added to {} file{}.'.
                     format(num_files_updated, pluralize(num_files_updated)))
    else:
        msg = ('Unable to determine the batch id from the output of '
               'et_put.py:\n{}'.format('\n'.join(cmd_output)))
        logger.error(msg)
        raise RuntimeError(msg)


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description="Move any data submissions "
                                                 "that haven't already been, "
                                                 "to elastic tape")
    parser.add_argument('-o', '--overwrite', help='write the submission to '
                                                  'elastic tape, even if the '
                                                  'submission has already '
                                                  'been written to tape',
                        action='store_true')
    parser.add_argument('-l', '--log-level', help='set logging level to one '
                                                  'of debug, info, warn (the '
                                                  'default), or error')
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    status_to_process = STATUS_VALUES['VALIDATED']

    # find all data submissions that have been validated and contain no
    # datafiles that have a tape_url
    # submissions = (DataSubmission.objects.annotate(Count('datafile__tape_url')).
    #     filter(status=status_to_process, datafile__tape_url__count=0))
    submissions = DataSubmission.objects.filter(
        incoming_directory='/group_workspaces/jasmin2/primavera4/upload/'
                           'CNRM-CERFACS/CNRM-CM6-1/incoming/v20170606'
    )

    for submission in submissions:
        submission_to_tape(submission.incoming_directory, args.overwrite)


if __name__ == '__main__':
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
