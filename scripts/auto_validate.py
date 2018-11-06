#!/usr/bin/env python
"""
auto_validate.py

This script is run by a cron job. It checks the ownership of the files in
DataSubmissions with a status of PENDING_PROCESSING and if they are all now
owned by the administrator then it submits a LOTUS job to run the validation.
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import argparse
import logging.config
import os
import pwd
import stat
import subprocess
import sys

import django
django.setup()
from pdata_app.utils.common import list_files
from pdata_app.models import DataSubmission, Settings
from vocabs.vocabs import STATUS_VALUES

__version__ = '0.1.0b1'

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


STATUS_TO_PROCESS = STATUS_VALUES['PENDING_PROCESSING']
ADMIN_USER = Settings.get_solo().contact_user_id
PARALLEL_SCRIPT = ('/home/users/jseddon/primavera/LIVE-prima-dm/scripts/'
                   'parallel_primavera')
VALIDATE_SCRIPT = 'validate_data_submission.py'
MAX_VALIDATE_SCRIPTS = 3
NUM_PROCS_USE_LOTUS = 4
LOTUS_OPTIONS = ('-o ~/lotus/%J.o -q par-multi -n {} -R "span[hosts=1]" '
                 '-W 24:00 -R "rusage[mem=98304.0]" -M 98304'.
                 format(NUM_PROCS_USE_LOTUS))
VERSION_STRING = 'v00000000'


def is_max_jobs_reached(job_name, max_num_jobs):
    """
    Check if the maximum number of jobs has been reached.

    :param str job_name: a component of the job name to check
    :param int max_num_jobs: the maximum number of jobs that can run
    :returns: True if `max_num_jobs` with `name` are running
    """
    cmd_out = subprocess.run(['bjobs', '-w'], stdout=subprocess.PIPE)

    if cmd_out.returncode:
        logger.error('bjobs returned code {}. Assuming the maximum number of '
                     'jobs has been reached.'.format(cmd_out.returncode))
        return True

    num_jobs = 0
    for line in cmd_out.stdout.decode('utf-8').split('\n'):
        if job_name in line:
            num_jobs += 1

    logger.debug('{} {} jobs running'.format(num_jobs, job_name))

    if num_jobs >= max_num_jobs:
        return True
    else:
        return False


def are_files_chowned(submission):
    """
    Check whether all of the files in the submission's directory are now
    owned by the admin user (they will be owned by the submitting user until
    the cron job has chowned them). If there are no files in the directory then
    return false.

    :param pdata_app.models.DataSubmission submission:
    :returns: True if all files in the submission's directory are owned by the
        admin user.
    """
    file_names = list_files(submission.directory)

    if not file_names:
        return False
    else:
        for file_name in file_names:
            uid = os.stat(file_name)[stat.ST_UID]
            user_name = pwd.getpwuid(uid)[0]

            if user_name != ADMIN_USER:
                return False

    return True


def submit_validation(submission_directory):
    """
    Submit a LOTUS job to run the validation.

    :param str submission_directory: The full path to the directory to
        validate.
    """
    cmd_cmpts = [
        'bsub',
        LOTUS_OPTIONS,
        PARALLEL_SCRIPT,
        VALIDATE_SCRIPT,
        '--log-level',
        'DEBUG',
        '--processes',
        '{}'.format(NUM_PROCS_USE_LOTUS),
        '--version-string',
        VERSION_STRING,
        submission_directory
    ]

    cmd = ' '.join(cmd_cmpts)

    logger.debug('Command is:\n{}'.format(cmd))

    bsub_out = subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, shell=True)

    if bsub_out.returncode:
        logger.error('Non-zero return code {} from:\n{}\n{}'.
                     format(bsub_out.returncode, ' '.join(cmd),
                            bsub_out.stderr.decode('utf-8')))
    else:
        logger.debug('Submission submitted for directory: {}\n{}'.
                     format(submission_directory,
                            bsub_out.stdout.decode('utf-8')))


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Automatically perform '
                                                 'PRIMAVERA tape writes.')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
                                                  'debug, info, warn (the '
                                                  'default), or error')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main():
    """
    Main entry point
    """
    logger.debug('Starting auto_validate.py')

    if is_max_jobs_reached(VALIDATE_SCRIPT, MAX_VALIDATE_SCRIPTS):
        logger.debug('Maximum number of jobs reached.')
        sys.exit(0)

    submissions = DataSubmission.objects.filter(status=STATUS_TO_PROCESS)

    logger.debug('{} submissions to validate found'.format(submissions.count()))

    for submission in submissions:
        if not are_files_chowned(submission):
            logger.debug('Skipping {} as all files not owned by {}.'.
                         format(submission.incoming_directory,
                                ADMIN_USER))
        else:
            logger.debug('Processing {}'.format(submission))
            submission.status = STATUS_VALUES['ARRIVED']
            submission.save()
            submit_validation(submission.incoming_directory)


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
    main()
