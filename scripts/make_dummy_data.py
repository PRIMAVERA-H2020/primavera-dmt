#!/usr/bin/env python
"""
make_dummy_data.py

Uses test_dataset.py to create some dummy files with a .nc extension. A dummy
data submission is created, which contains these files. Dummy data requests
that would be completely and partially fulfilled by these files are also
created. The data created uses unrealistic variable and model names, which
prevents it from getting tangled up with live data from the genuine
VariableRequests.

The reset_db.sh script can be used by the user to clear the database before
running this script if desired.
"""
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

import os
import re

import cf_units
import cftime

import test.test_datasets as datasets
from pdata_app.utils.dbapi import get_or_create, match_one
from pdata_app.models import (DataSubmission, DataFile, ClimateModel,
    Experiment, Project, ESGFDataset, CEDADataset, DataRequest,
    Institute, VariableRequest, DataIssue)
from vocabs import STATUS_VALUES, FREQUENCY_VALUES, VARIABLE_TYPES, CALENDARS


TIME_UNITS = 'days since 1900-01-01'
CALENDAR=CALENDARS['360_day']


def make_data_request():
    """
    Create a DataRequest that matches files in the later submission
    """
    # Make the variable chips from the Monty model for which all data is available
    project = get_or_create(Project, short_name='CMIP6',
        full_name='Coupled Model Intercomparison Project Phase 6')
    institute = get_or_create(Institute, short_name='MOHC', full_name='Met Office Hadley Centre')
    climate_model = get_or_create(ClimateModel, short_name='Monty', full_name='Really good model')
    experiment = get_or_create(Experiment, short_name='rcp45', full_name='Really good experiment')
    var_req = get_or_create(VariableRequest, table_name='cfDay',
        long_name='Really good variable', units='1', var_name='chips',
        standard_name='really_good_variable', cell_methods='time:mean',
        positive='optimistic', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='chips', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['day'], cell_measures='', uid='123abc')

    data_req = get_or_create(DataRequest, project=project, institute=institute,
        climate_model=climate_model, experiment=experiment,
        variable_request=var_req,
        start_time=_cmpts2num(1991, 1, 1, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        end_time=_cmpts2num(1993, 12, 30, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        time_units = TIME_UNITS, calendar=CALENDAR)

    # Make the variable spam from the Python model for which one year is missing
    institute = get_or_create(Institute, short_name='IPSL', full_name='Institut Pierre Simon Laplace')
    climate_model = get_or_create(ClimateModel, short_name='Python', full_name='Really good model')
    experiment = get_or_create(Experiment, short_name='abrupt4xCO2', full_name='Really good experiment')
    var_req = get_or_create(VariableRequest, table_name='cfDay',
        long_name='Really good variable', units='1', var_name='spam',
        standard_name='really_good_variable', cell_methods='time:mean',
        positive='optimistic', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='spam', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['day'], cell_measures='', uid='123abc')

    data_req = get_or_create(DataRequest, project=project, institute=institute,
        climate_model=climate_model, experiment=experiment,
        variable_request=var_req,
        start_time=_cmpts2num(1991, 1, 1, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        end_time=_cmpts2num(1994, 12, 30, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        time_units=TIME_UNITS, calendar=CALENDAR)

    # Make two requests that are entirely missing
    var_req = get_or_create(VariableRequest, table_name='Aday',
        long_name='Really good variable', units='1', var_name='pie',
        standard_name='really_good_variable', cell_methods='time:mean',
        positive='optimistic', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='pie', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['day'], cell_measures='', uid='123abc')

    data_req = get_or_create(DataRequest, project=project, institute=institute,
        climate_model=climate_model, experiment=experiment,
        variable_request=var_req,
        start_time=_cmpts2num(1991, 1, 1, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        end_time=_cmpts2num(1994, 12, 30, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        time_units=TIME_UNITS, calendar=CALENDAR)

    var_req = get_or_create(VariableRequest, table_name='Aday',
        long_name='Really good variable', units='1', var_name='cake',
        standard_name='really_good_variable', cell_methods='time:mean',
        positive='optimistic', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='cake', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['day'], cell_measures='', uid='123abc')

    data_req = get_or_create(DataRequest, project=project, institute=institute,
        climate_model=climate_model, experiment=experiment,
        variable_request=var_req,
        start_time=_cmpts2num(1991, 1, 1, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        end_time=_cmpts2num(1994, 12, 30, 0, 0, 0, 0, TIME_UNITS, CALENDAR),
        time_units=TIME_UNITS, calendar=CALENDAR)

    # generate variable requests for the remaining files in the later submission
    var_req = get_or_create(VariableRequest, table_name='day',
        long_name='Really good variable', units='1', var_name='beans',
        standard_name='really_good_variable', cell_methods='time:mean',
        positive='smelly', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='beans', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['day'], cell_measures='', uid='123abc')


def make_data_submission():
    """
    Create a Data Submission and add files to it
    """
    test_dsub = datasets.test_data_submission
    test_dsub.create_test_files()

    dsub = get_or_create(DataSubmission, status=STATUS_VALUES.ARRIVED,
               incoming_directory=test_dsub.INCOMING_DIR,
               directory=test_dsub.INCOMING_DIR, user='primavera')

    for dfile_name in test_dsub.files:
        path = os.path.join(test_dsub.INCOMING_DIR, dfile_name)
        metadata = _extract_file_metadata(path)

        proj = get_or_create(Project, short_name="CMIP6", full_name="Coupled Model Intercomparison Project Phase 6")
        climate_model = get_or_create(ClimateModel, short_name=metadata["climate_model"], full_name="Really good model")
        experiment = get_or_create(Experiment, short_name=metadata["experiment"], full_name="Really good experiment")
        institute = get_or_create(Institute, short_name="MOHC", full_name="Met Office Hadley Centre")

        var_match = match_one(VariableRequest, cmor_name=metadata['var_id'],
                              table_name=metadata['table'])
        if var_match:
            variable = var_match
        else:
            msg = ('No variable request found for file: {}. Please create a '
                   'variable request and resubmit.'.format(dfile_name))
            print('ERROR: ' + msg)
            raise ValueError(msg)

        _dfile = DataFile.objects.create(name=dfile_name, incoming_directory=test_dsub.INCOMING_DIR,
            directory=test_dsub.INCOMING_DIR, size=os.path.getsize(path),
            project=proj, climate_model=climate_model, institute=institute,
            experiment=experiment, frequency=metadata["frequency"],
            rip_code=metadata["ensemble"], variable_request=variable,
            start_time=metadata["start_time"], end_time=metadata["end_time"],
            time_units=metadata['time_units'], calendar=metadata['calendar'],
            data_submission=dsub, online=True)

    ceda_ds = get_or_create(CEDADataset, catalogue_url='http://www.metoffice.gov.uk',
        directory=test_dsub.INCOMING_DIR)

    esgf_ds = get_or_create(ESGFDataset, drs_id='ab.cd.ef.gh', version='v19160519',
        directory=test_dsub.INCOMING_DIR, data_submission=dsub, ceda_dataset=ceda_ds)

    for df in dsub.get_data_files():
        df.esgf_dataset = esgf_ds
        df.ceda_dataset = ceda_ds
        df.ceda_download_url = 'http://browse.ceda.ac.uk/browse/badc/cmip5/' + df.name
        df.ceda_opendap_url = 'http://dap.ceda.ac.uk/data/badc/cmip5/some/dir/' + df.name
        df.esgf_opendap_url = 'http://esgf.ceda.ac.uk/data/badc/cmip5/some/dir/' + df.name
        df.esgf_download_url = 'http://esgf.ceda.ac.uk/browse/badc/cmip5/' + df.name
        df.save()

    dsub.status = STATUS_VALUES.ARCHIVED
    dsub.save()


def make_data_issue():
    """
    Create a dummy data issue
    """
    di = get_or_create(DataIssue, issue='Beans are good for your heart',
        reporter='Jon Seddon',
        date_time=_cmpts2num(2016, 9, 2, 14, 38, 49, 0, TIME_UNITS, CALENDAR),
        time_units=TIME_UNITS, calendar=CALENDAR)

    bean_files = DataFile.objects.filter(name__istartswith='beans_')
    for data_file in bean_files:
        di.data_file.add(data_file)
        di.save()


def main():
    make_data_request()
    make_data_submission()
    make_data_issue()


def _extract_file_metadata(file_path):
    """
    Extracts metadata from file name and returns dictionary.
    """
    # e.g. tasmax_day_IPSL-CM5A-LR_amip4K_r1i1p1_18590101-18591230.nc
    keys = ("var_id", "table", "climate_model", "experiment", "ensemble",
        "time_range")

    items = os.path.splitext(os.path.basename(file_path))[0].split("_")
    data = {}

    for i in range(len(items)):
        key = keys[i]
        value = items[i]

        if key == "time_range":
            start_time, end_time = value.split("-")

            data["start_time"] = cf_units.date2num(
                _date_from_string(start_time), TIME_UNITS, CALENDAR)

            data["end_time"] = cf_units.date2num(
                _date_from_string(end_time), TIME_UNITS, CALENDAR)

            data["time_units"] = TIME_UNITS
            data["calendar"] = CALENDAR

        elif key == "table":
            data['table'] = value
            for fv in FREQUENCY_VALUES:
                if fv.lower() in value.lower():
                    data['frequency'] = fv
                    break
            if 'frequency' not in data:
                data['frequency'] = ''
        else:
            data[key] = value

    return data


def _date_from_string(date_str):
    """
    Make a datetime like object from a string in the form YYYYMMDD

    :param date_str: The string to convert
    :return: A datetime like object
    :raises ValueError: if unable to parse `date_str`
    """
    if len(date_str) != 8:
        msg = 'Date string does not contain 8 characters: {}'.format(date_str)
        raise ValueError(msg)
    components = re.match(r'(\d{4})(\d{2})(\d{2})', date_str)

    if components:
        date_obj = cftime.datetime(int(components.group(1)),
            int(components.group(2)), int(components.group(3)))
    else:
        msg = 'Unable to parse date string (expecting YYYYMMDD): {}'.format(
            date_str)
        raise ValueError(msg)

    return date_obj


def _cmpts2num(year, month, day, hour, minute, second, microsecond, time_units,
        calendar):
    """
    Convert the specified date and time into a floating point number relative to
    `time_units`.

    :param int year: The year
    :param int month: The month
    :param int day: The day
    :param int hour: The hour
    :param int minute: The minute
    :param int second: The second
    :param int microsecond: The microsecond
    :param str time_units: A string representing the time units to use
    :param str calendar: The calendar to use
    :returns: The specified date as a floating point number relative to
        `time_units`
    """
    dt_obj = cftime.datetime(year, month, day, hour, minute,
        second, microsecond)

    return cf_units.date2num(dt_obj, time_units, calendar)


if __name__ == "__main__":
    main()
