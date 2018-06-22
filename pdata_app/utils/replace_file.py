"""
replace_file.py - a function to move DataFile entries to a ReplacedFile entry.
"""
from __future__ import unicode_literals, division, absolute_import

import logging.config
from pdata_app.models import DataFile, ReplacedFile

logger = logging.getLogger(__name__)


def replace_files(queryset):
    """
    Move DataFile entries from `queryset` to a ReplacedFile type

    :param django.db.models.query.QuerySet queryset: the DataFile objects to
        move.
    :raises TypeError: if a queryset entry is not a DataFile.
    :raises ValueError: if unable to create a ReplacedFile object
    """
    num_files_moved = 0

    for datafile in queryset:
        if not isinstance(datafile, DataFile):
            raise TypeError('queryset entries must be of type DataFile')

        checksum = datafile.checksum_set.first()
        replacement_file = ReplacedFile.objects.create(
            name=datafile.name,
            incoming_directory=datafile.incoming_directory,
            size=datafile.size,
            version=datafile.version,
            project=datafile.project,
            institute=datafile.institute,
            climate_model=datafile.climate_model,
            activity_id=datafile.activity_id,
            experiment=datafile.experiment,
            variable_request=datafile.variable_request,
            data_request=datafile.data_request,
            frequency=datafile.frequency,
            rip_code=datafile.rip_code,
            grid=datafile.grid,
            start_time=datafile.start_time,
            end_time=datafile.end_time,
            time_units=datafile.time_units,
            calendar=datafile.calendar,
            data_submission=datafile.data_submission,
            tape_url=datafile.tape_url,
            checksum_value=checksum.checksum_value if checksum else None,
            checksum_type=checksum.checksum_type if checksum else None
        )

        if replacement_file:
            datafile.delete()
            num_files_moved += 1
        else:
            raise ValueError('No ReplacedFile object created for {}.'.
                             format(datafile))

    logger.debug('{} files moved.'.format(num_files_moved))
