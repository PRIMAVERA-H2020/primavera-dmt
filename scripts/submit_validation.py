#!/usr/bin/env python
"""
submit_validation.py

This script is run by a cron job. It checks the ownership of the files in
DataSubmissions with a status of PENDING_PROCESSING and if they are all now
owned by the administrator then it submits a LOTUS job to run the validation.
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

import os
import pwd
import stat
import subprocess

import django
django.setup()
from pdata_app.models import DataSubmission
from vocabs.vocabs import STATUS_VALUES

STATUS_TO_PROCESS = STATUS_VALUES['PENDING_PROCESSING']
ADMIN_USER = 'jseddon'
PARALLEL_SCRIPT = ('/home/users/jseddon/primavera/primavera-dmt/scripts/'
    'parallel_primavera')
VALIDATE_SCRIPT = 'validate_data_submission.py'
NUM_PROCS_USE_LOTUS = 8
LOTUS_OPTIONS = ('-o ~/lotus/%J.o -q par-single -n {} -R "span[hosts=1]" '
                 '-W 01:00'.format(NUM_PROCS_USE_LOTUS))

def are_files_chowned(submission):
    """
    Check whether all of the netCDF files in the submission's directory are now
    owned by the admin user (they will be owned by the submitting user until
    the cron job has chowned them). If there are no files in the directory then
    return false.

    :param pdata_app.models.DataSubmission submission:
    :return: True if all files in the submission's directory are owned by the
        administrator
    """
    file_names = list_files(submission.directory)

    if file_names:
        for file_name in file_names:
            uid = os.stat(file_name)[stat.ST_UID]
            user_name = pwd.getpwuid(uid)[0]

            if user_name != ADMIN_USER:
                return False

    return True


def submit_validation(submission):
    """
    Submit a LOTUS job to run the validation.

    :param submission:
    :return:
    """
    cmd = 'bsub {} {} {} --log-level DEBUG --processes {} {}'.format(
        LOTUS_OPTIONS, PARALLEL_SCRIPT, VALIDATE_SCRIPT, NUM_PROCS_USE_LOTUS,
        submission)
    bsub_output = subprocess.check_output(cmd, shell=True)
    print('Submission: {}'.format(submission))
    print(bsub_output)



def list_files(directory, suffix='.nc'):
    """
    Return a list of all the files with the specified suffix in the submission
    directory structure and sub-directories.

    :param str directory: The root directory of the submission
    :param str suffix: The suffix of the files of interest
    :returns: A list of absolute filepaths
    """
    nc_files = []

    dir_files = os.listdir(directory)
    for filename in dir_files:
        file_path = os.path.join(directory, filename)
        if os.path.isdir(file_path):
            nc_files.extend(list_files(file_path))
        elif file_path.endswith(suffix):
            nc_files.append(file_path)

    return nc_files


def main():
    submissions = DataSubmission.objects.filter(status=STATUS_TO_PROCESS)

    for submission in submissions:
        if are_files_chowned(submission):
            submission.status = STATUS_VALUES['ARRIVED']
            submission.save()
            submit_validation(submission.directory)


if __name__ == "__main__":
    main()
