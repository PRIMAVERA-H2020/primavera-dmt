#!/usr/bin/env python
"""
update_dreqs_0319.py

ESGF AttributeUpdate
Called from a Rose suite to update the mip_era in EC-Earth r1i1p1f1 datasets.
"""
import argparse
import logging.config
import os
import sys

import django
django.setup()

from pdata_app.models import DataFile, DataRequest, Project, Settings  # nopep8
from pdata_app.utils.attribute_update import MipEraUpdate  # nopep8
from pdata_app.utils.common import adler32, delete_files  # nopep8


__version__ = '0.1.0b1'

logger = logging.getLogger(__name__)

# Directory to copy the file to, to run the attribute edits
SCRATCH_DIR = "/work/scratch-nopw/jseddon/temp"
# The top-level directory to write output data to
BASE_OUTPUT_DIR = Settings.get_solo().base_output_dir


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Update institution_id')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('-i', '--incoming', help='Update file only, not the '
                                                 'database.',
                        action='store_true')
    parser.add_argument('request_id', help='to request id to update')
    parser.add_argument('-s', '--skip-checksum', help='skip checking checksums',
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    model, expt, var_lab, table, var = args.request_id.split('_')

    dreq = DataRequest.objects.get(
        project__short_name='CMIP6',
        climate_model__short_name=model,
        experiment__short_name=expt,
        rip_code=var_lab,
        variable_request__table_name=table,
        variable_request__cmor_name=var
    )
    logger.debug('DataRequest is {}'.format(dreq))

    if not args.skip_checksum:
        logger.debug('Checking checksums')
        checksum_mismatch = 0
        for data_file in dreq.datafile_set.order_by('name'):
            logger.debug('Processing {}'.format(data_file.name))
            full_path = os.path.join(data_file.directory, data_file.name)
            actual = adler32(full_path)
            if data_file.tapechecksum_set.count():
                expected = data_file.tapechecksum_set.first().checksum_value
            else:
                expected = data_file.checksum_set.first().checksum_value
            if actual != expected:
                logger.error(f'Checksum mismatch for {full_path}')
                checksum_mismatch += 1
                dfs = DataFile.objects.filter(name=data_file.name)
                if dfs.count() != 1:
                    logger.error(f'Unable to select file for deletion {full_path}')
                else:
                    delete_files(dfs.all(), BASE_OUTPUT_DIR)
        if checksum_mismatch:
            logger.error(f'Exiting due to {checksum_mismatch} checksum failures.')
            logger.error(f'Data request is in {dreq.directories()}')
            sys.exit(1)
    

    logger.debug('Processing files')
    for data_file in dreq.datafile_set.order_by('name'):
        logger.debug('Processing {}'.format(data_file.name))

        new_mip_era = 'PRIMAVERA'

        new_dreq, created = DataRequest.objects.get_or_create(
            project=Project.objects.get(short_name=new_mip_era),
            institute=dreq.institute,
            climate_model=dreq.climate_model,
            experiment=dreq.experiment,
            variable_request=dreq.variable_request,
            rip_code=dreq.rip_code,
            request_start_time=dreq.request_start_time,
            request_end_time=dreq.request_end_time,
            time_units=dreq.time_units,
            calendar=dreq.calendar
        )
        if created:
            logger.debug('Created {}'.format(new_dreq))

        updater = MipEraUpdate(data_file, new_mip_era,
                               update_file_only=args.incoming,
                               temp_dir=SCRATCH_DIR)
        updater.update()

        if dreq.datafile_set.count() == 0:
            logger.debug(f'DataRequest has no files so deleting CMIP6 {dreq}')
            try:
                dreq.delete()
            except django.db.models.deletion.ProtectedError:
                dreq.rip_code = 'r9i9p9f9'
                dreq.save()


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
