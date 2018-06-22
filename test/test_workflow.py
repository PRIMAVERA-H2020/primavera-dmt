"""
Use unit tests to represent example workflows in the data management tool.

The workflows that will occur are documented in:
https://docs.google.com/document/d/1qnIg2pHqF1I1tuP_iCVzb6yL_bXZoheBBUQ9RuGWPlQ
"""
import datetime
import os
import re

import cf_units
import netcdftime
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import get_runner
from django.utils.timezone import make_aware

import test.test_datasets as datasets

from vocabs.vocabs import (FREQUENCY_VALUES, STATUS_VALUES, VARIABLE_TYPES,
    CALENDARS)
from pdata_app.utils.dbapi import get_or_create
from pdata_app.models import (ClimateModel, Institute, Experiment, Project,
    DataSubmission, DataFile, DataRequest, ESGFDataset, CEDADataset,
    DataIssue, Settings, VariableRequest, ActivityId)


TIME_UNITS = 'days since 1900-01-01'
CALENDAR = CALENDARS['360_day']


# Utility functions for test workflow
def _empty_test_data_dirs():
    dir_types = ("incoming", "archive", "esgf")

    for dir_type in dir_types:
        dr = os.path.join('.', 'test_data', dir_type)
        for fname in os.listdir(dr):
            os.remove(os.path.join(dr, fname))


def _create_test_data_dirs():
    dir_types = ("incoming", "archive", "esgf")

    for dir_type in dir_types:
        dr = os.path.join('.', 'test_data', dir_type)
        if not os.path.isdir(dr): os.makedirs(dr)


def _extract_file_metadata(file_path):
    "Extracts metadata from file name and returns dictionary."
    # e.g. tasmax_day_IPSL-CM5A-LR_amip4K_r1i1p1_18590101-18591230.nc
    keys = ("var_id", "table", "climate_model", "experiment", "ensemble", "time_range")

    items = os.path.splitext(os.path.basename(file_path))[0].split("_")
    data = {}

    for i in range(len(items)):
        key = keys[i]
        value = items[i]

        if key == "time_range":
            start_time, end_time = value.split("-")
            data["start_time"] = cf_units.date2num(_date_from_string(start_time), TIME_UNITS, CALENDAR)
            data["end_time"] = cf_units.date2num(_date_from_string(end_time), TIME_UNITS, CALENDAR)
            data["time_units"] = TIME_UNITS
            data["calendar"] = CALENDAR
        else:
            data[key] = value

    return data


class PdataBaseTest(TestCase):

    @classmethod
    def setUpClass(self):
        _create_test_data_dirs()

    @classmethod
    def tearDownClass(self):
        # Empty data dirs
        _empty_test_data_dirs()


class TestWorkflows(PdataBaseTest):
    def setUp(self):
        # Set up global settings
        self.settings = Settings.objects.create(is_paused=False)

    def tearDown(self):
        pass

    def test_01_data_request(self):
        project = get_or_create(Project, short_name='CMIP6',
            full_name='Coupled Model Intercomparison Project Phase 6')
        institute = get_or_create(Institute, short_name='u', full_name='University')
        climate_model = get_or_create(ClimateModel, short_name='my_model', full_name='Really big model')
        experiment = get_or_create(Experiment, short_name='my_expt', full_name='Really detailed experiment')
        var_req = get_or_create(VariableRequest, table_name='Amon',
            long_name='very descriptive', units='1', var_name='var1',
            standard_name='var_name', cell_methods='time:mean',
            positive='optimistic', variable_type=VARIABLE_TYPES['real'],
            dimensions='massive', cmor_name='var1', modeling_realm='atmos',
            frequency=FREQUENCY_VALUES['ann'], cell_measures='', uid='123abc')

        data_req = get_or_create(DataRequest, project=project, institute=institute,
            climate_model=climate_model, experiment=experiment,
            variable_request=var_req,
            request_start_time=_cmpts2num(1900, 1, 1, 0, 0, 0, 0,
                                          TIME_UNITS, CALENDAR),
            request_end_time=_cmpts2num(2000, 1, 1, 0, 0, 0, 0,
                                        TIME_UNITS, CALENDAR))

        # Make some assertions
        data_req = DataRequest.objects.all()[0]
        self.assertEqual(data_req.institute.full_name, 'University')
        self.assertEqual(data_req.climate_model.short_name, 'my_model')
        self.assertEqual(data_req.experiment.short_name, 'my_expt')
        self.assertEqual(data_req.variable_request.cmor_name, 'var1')
        self.assertEqual(data_req.variable_request.modeling_realm, 'atmos')

    def test_02_data_submission(self):
        # Create a Data Submission and add files to it
        test_dsub = _make_data_submission()

        # Make some assertions
        for dfile_name in test_dsub.files:
            self.assertEqual(dfile_name, DataFile.objects.filter(name=dfile_name).first().name)

    def test_03_move_files_to_tape(self):
        test_dsub = _make_data_submission()

        data_submission = DataSubmission.objects.all()[0]

        for df in data_submission.get_data_files():
            df.tape_url = 'et:4037'
            df.online = False
            df.save()

        # Make some assertions
        for dfile_name in test_dsub.files:
            self.assertFalse(DataFile.objects.filter(name=dfile_name).first().online)
            self.assertEqual(DataFile.objects.filter(name=dfile_name).first().tape_url, 'et:4037')

    def test_04_restore_from_tape(self):
        # Do everything that was done for moving to tape
        test_dsub = _make_data_submission()

        data_submission = DataSubmission.objects.all()[0]

        for df in data_submission.get_data_files():
            df.tape_url = 'et:4037'
            df.online = False
            df.save()

        # Check that data was moved to tape
        for dfile_name in test_dsub.files:
            self.assertFalse(DataFile.objects.filter(name=dfile_name).first().online)
            self.assertEqual(DataFile.objects.filter(name=dfile_name).first().tape_url, 'et:4037')

        # Restore from tape
        for df in data_submission.get_data_files():
            df.online = True
            df.save()

        # Make some assertions to check that it's been restored
        for dfile_name in test_dsub.files:
            self.assertTrue(DataFile.objects.filter(name=dfile_name).first().online)
            # check that it's still held on tape
            self.assertEqual(DataFile.objects.filter(name=dfile_name).first().tape_url, 'et:4037')

    def test_05_create_data_issue(self):
        # Create a data submission to start with
        test_dsub = _make_data_submission()

        data_submission = DataSubmission.objects.all()[0]

        # Now, create the data issue
        reporter = get_or_create(User, username='Fred')
        data_issue = get_or_create(DataIssue, issue='test issue',
            reporter=reporter,
            date_time=make_aware(datetime.datetime(1978, 7, 19, 0, 0, 0, 0),
                                 pytz.UTC, None))

        # Add the issue to all files in the submission
        for df in data_submission.get_data_files():
            df.dataissue_set.add(data_issue)
            df.save()

        # Make some assertions
        for dfile_name in test_dsub.files:
            df = DataFile.objects.filter(name=dfile_name).first()
            self.assertEqual(df.dataissue_set.count(), 1)
            self.assertEqual(df.dataissue_set.first().issue, 'test issue')

    def test_06_ingest_to_ceda(self):
        # Create a ata submission to start with
        test_dsub = _make_data_submission()

        data_submission = DataSubmission.objects.all()[0]

        # Create a CEDA data set
        ceda_ds = get_or_create(CEDADataset, doi='doi:10.2514/1.A32039',
            catalogue_url='http://catalogue.ceda.ac.uk/uuid/85c7d0b09c974bd6abb07a324c2f427b',
            directory='/badc/some/dir')

        for df in data_submission.get_data_files():
            df.ceda_dataset = ceda_ds
            df.ceda_opendap_url = 'http://dap.ceda.ac.uk/data/badc/cmip5/some/dir/' + df.name
            df.ceda_download_url = 'http://browse.ceda.ac.uk/browse/badc/cmip5/' + df.name
            df.save()

        # Make some assertions
        for dfile_name in test_dsub.files:
            df = DataFile.objects.filter(name=dfile_name).first()
            self.assertEqual(df.ceda_dataset.doi, 'doi:10.2514/1.A32039')
            self.assertEqual(df.ceda_download_url, 'http://browse.ceda.ac.uk/browse/badc/cmip5/' + df.name)

    def test_07_publish_to_esgf(self):
        # Create a ata submission to start with
        test_dsub = _make_data_submission()

        data_submission = DataSubmission.objects.all()[0]

        # Ingest into CEDA
        ceda_ds = get_or_create(CEDADataset, doi='doi:10.2514/1.A32039',
            catalogue_url='http://catalogue.ceda.ac.uk/uuid/85c7d0b09c974bd6abb07a324c2f427b',
            directory='/badc/some/dir')

        for df in data_submission.get_data_files():
            df.ceda_dataset = ceda_ds
            df.ceda_opendap_url = 'http://dap.ceda.ac.uk/data/badc/cmip5/some/dir/' + df.name
            df.ceda_download_url = 'http://browse.ceda.ac.uk/browse/badc/cmip5/' + df.name
            df.save()

        # Create an ESGF data set
        esgf_ds = get_or_create(ESGFDataset, drs_id='a.b.c.d', version='v20160720',
            directory='/some/dir', ceda_dataset=ceda_ds,
            data_submission=data_submission)

        # Update each file
        for df in data_submission.get_data_files():
            df.esgf_dataset = esgf_ds
            df.esgf_opendap_url = 'http://esgf.ceda.ac.uk/data/badc/cmip5/some/dir/' + df.name
            df.esgf_download_url = 'http://esgf.ceda.ac.uk/browse/badc/cmip5/' + df.name
            df.save()

        # Make some assertions
        for dfile_name in test_dsub.files:
            df = DataFile.objects.filter(name=dfile_name).first()
            self.assertEqual(df.esgf_dataset.get_full_id(), 'a.b.c.d.v20160720')
            self.assertEqual(df.esgf_download_url, 'http://esgf.ceda.ac.uk/browse/badc/cmip5/' + df.name)
            self.assertEqual(df.esgf_dataset.data_submission.directory, './test_data/submission')

def _make_data_submission():
    """
    Create files and a data submission. Returns an DataSubmissionForTests
    object.
    """
    test_dsub = datasets.test_data_submission
    test_dsub.create_test_files()

    user = get_or_create(User, username='fred')
    dsub = get_or_create(DataSubmission, status=STATUS_VALUES.ARRIVED,
               incoming_directory=test_dsub.INCOMING_DIR,
               directory=test_dsub.INCOMING_DIR, user=user)

    for dfile_name in test_dsub.files:
        path = os.path.join(test_dsub.INCOMING_DIR, dfile_name)
        m = metadata = _extract_file_metadata(path)

        proj = get_or_create(Project, short_name="CMIP6", full_name="6th Coupled Model Intercomparison Project")
        climate_model = get_or_create(ClimateModel, short_name=m["climate_model"], full_name="Really good model")
        institute = get_or_create(Institute, short_name='MOHC',
            full_name='Met Office Hadley Centre')
        experiment = get_or_create(Experiment, short_name=m["experiment"], full_name="Really good experiment")
        var = get_or_create(VariableRequest, table_name=metadata['table'],
            long_name='very descriptive', units='1', var_name=metadata['var_id'],
            standard_name='var_name', cell_methods='time: mean',
            positive='optimistic', variable_type=VARIABLE_TYPES['real'],
            dimensions='massive', cmor_name=metadata['var_id'],
            modeling_realm='atmos', frequency=FREQUENCY_VALUES['ann'],
            cell_measures='', uid='123abc')
        dreq = get_or_create(DataRequest, project=proj, institute=institute,
            climate_model=climate_model, experiment=experiment,
            variable_request=var, rip_code='r1i1p1f1', request_start_time=0.0,
            request_end_time=23400.0, time_units='days since 1950-01-01',
            calendar='360_day')
        act_id = get_or_create(ActivityId, short_name='HighResMIP',
            full_name='High Resolution Model Intercomparison Project')

        dfile = DataFile.objects.create(name=dfile_name, incoming_directory=test_dsub.INCOMING_DIR,
            directory=test_dsub.INCOMING_DIR, size=os.path.getsize(path),
            project=proj, climate_model=climate_model, institute=institute,
            experiment=experiment, variable_request=var, data_request=dreq,
            frequency=FREQUENCY_VALUES['ann'], rip_code=m["ensemble"],
            activity_id=act_id, start_time=m["start_time"],
            end_time=m["end_time"], time_units=m["time_units"],
            calendar=m["calendar"], data_submission=dsub, online=True)

    return test_dsub


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
        date_obj = netcdftime.datetime(int(components.group(1)), int(components.group(2)),
            int(components.group(3)))
    else:
        msg = 'Unable to parse date string (expecting YYYYMMDD): {}'.format(date_str)
        raise ValueError(msg)

    return date_obj


def _cmpts2num(year, month, day, hour, minute, second, microsecond, time_units, calendar):
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
    dt_obj = netcdftime.datetime(year, month, day, hour, minute,
        second, microsecond)

    return cf_units.date2num(dt_obj, time_units, calendar)


if __name__ == "__main__":

    limited_suite = True

    tests = ['test_01_data_request', 'test_02_data_submission',
        'test_03_move_files_to_tape', 'test_04_restore_from_tape',
        'test_05_create_data_issue', 'test_06_ingest_to_ceda',
        'test_07_publish_to_esgf']

    full_test_names = ['test.test_workflow.TestWorkflows.' + t for t in tests]

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)

    if limited_suite:
        test_runner.run_tests(full_test_names)
    else:
        test_runner.run_tests(['test.test_workflow.TestWorkflows'])