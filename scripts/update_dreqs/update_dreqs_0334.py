#!/usr/bin/env python
"""
update_dreqs_0334.py

ESGF AttributeUpdate
Update the mip_era in WP5 datasets, many datasets at a time.
"""
import argparse
import logging.config
import os

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
    parser = argparse.ArgumentParser(description='Update mip_era')
    parser.add_argument('-l', '--log-level',
                        help='set logging level (default: %(default)s)',
                        choices=['debug', 'info', 'warning', 'error'],
                        default='warning')
    parser.add_argument('-i', '--incoming', help='Update file only, not the '
                                                 'database.',
                        action='store_true')
    parser.add_argument('variant_label', help='the variant label to update')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    args = parser.parse_args()

    return args


def main(args):
    """
    Main entry point
    """
    dreqs = DataRequest.objects.filter(
        project__short_name='CMIP6',
        climate_model__short_name='EC-Earth3P',
        experiment__short_name__contains='primWP5-amv',
        rip_code=args.variant_label
    ).distinct()

    dreq_ids = list(dreqs.values_list('id', flat=True))

    for dreq_id in dreq_ids:
        dreq = DataRequest.objects.get(id=dreq_id)

        logger.debug(f'DataRequest is {dreq}')

        logger.debug('Checking checksums')
        checksum_mismatch = 0
        for data_file in dreq.datafile_set.order_by('name'):
            logger.debug('Processing {}'.format(data_file.name))
            full_path = os.path.join(data_file.directory, data_file.name)
            actual = adler32(full_path)
            expected = data_file.checksum_set.first().checksum_value
            if actual != expected:
                logger.error(f'Checksum mismatch for {full_path}')
                checksum_mismatch += 1
                dfs = DataFile.objects.filter(name=data_file.name)
                if dfs.count() != 1:
                    logger.error(f'Unable to select file for deletion '
                                 f'{full_path}')
                else:
                    delete_files(dfs.all(), BASE_OUTPUT_DIR)
        if checksum_mismatch:
            logger.error(f'{checksum_mismatch} checksum failures in {dreq}.')
            continue

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
                logger.debug(f'DataRequest has no files so deleting CMIP6 '
                             f'{dreq}')
                dreq.delete()


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
