#!/usr/bin/env python
"""
create_root_chown_list.py

This script is run by a cron job. It finds the DataSubmission's with a status
of PENDING_PROCESSING and writes their top-level directory path to a file. This
file will then be read by another cron job running as CEDA root, which will
chown the files in the submission from the user who submitted them to the
PRIMAVERA DMT admin user.
"""
from __future__ import unicode_literals, division, absolute_import
from multiprocessing.pool import ThreadPool

try:
    import dask
except ImportError:
    pass
import iris

import django
django.setup()
from pdata_app.models import DataSubmission
from vocabs.vocabs import STATUS_VALUES

STATUS_TO_PROCESS = STATUS_VALUES['PENDING_PROCESSING']
OUTPUT_FILE = ('/home/users/jseddon/primavera/root_cron/'
               'primavera_chown_list.txt')


def main():
    # Limit the number of Dask threads
    if not iris.__version__.startswith('1.'):
        dask.config.set(pool=ThreadPool(2))

    submissions = DataSubmission.objects.filter(status=STATUS_TO_PROCESS)

    with open(OUTPUT_FILE, 'w') as fh:
        for submission in submissions:
            fh.write(submission.directory + '\n')


if __name__ == "__main__":
    main()
