"""
test_replace_file.py - unit tests for pdata_app.utils.replace_file.py
"""
from __future__ import unicode_literals, division, absolute_import

from django.contrib.auth.models import User
from django.test import TestCase
from pdata_app.models import (ActivityId, Checksum, ClimateModel, DataFile,
                              DataRequest, DataSubmission, Experiment,
                              Institute, Project, ReplacedFile, Settings,
                              VariableRequest)
from pdata_app.utils.dbapi import get_or_create
from pdata_app.utils.replace_file import replace_files
from vocabs.vocabs import (CALENDARS, FREQUENCY_VALUES, STATUS_VALUES,
                           VARIABLE_TYPES)


class TestReplaceFile(TestCase):
    def setUp(self):
        # create the necessary DB objects
        proj = get_or_create(Project, short_name="CMIP6", full_name="6th "
            "Coupled Model Intercomparison Project")
        climate_model = get_or_create(ClimateModel, short_name="MY-MODEL",
            full_name="Really good model")
        institute = get_or_create(Institute, short_name='MOHC',
            full_name='Met Office Hadley Centre')
        act_id = get_or_create(ActivityId, short_name='HighResMIP',
            full_name='High Resolution Model Intercomparison Project')
        experiment = get_or_create(Experiment, short_name="experiment",
            full_name="Really good experiment")
        incoming_directory = '/gws/MOHC/MY-MODEL/incoming/v12345678'
        var1 = get_or_create(VariableRequest, table_name='my-table',
            long_name='very descriptive', units='1', var_name='my-var',
            standard_name='var-name', cell_methods='time: mean',
            positive='optimistic', variable_type=VARIABLE_TYPES['real'],
            dimensions='massive', cmor_name='my-var', modeling_realm='atmos',
            frequency=FREQUENCY_VALUES['ann'], cell_measures='', uid='123abc')
        var2 = get_or_create(VariableRequest, table_name='your-table',
            long_name='very descriptive', units='1', var_name='your-var',
            standard_name='var-name', cell_methods='time: mean',
            positive='optimistic', variable_type=VARIABLE_TYPES['real'],
            dimensions='massive', cmor_name='your-var', modeling_realm='atmos',
            frequency=FREQUENCY_VALUES['ann'], cell_measures='', uid='123abc')
        self.dreq1 = get_or_create(DataRequest, project=proj,
            institute=institute, climate_model=climate_model,
            experiment=experiment, variable_request=var1, rip_code='r1i1p1f1',
            request_start_time=0.0, request_end_time=23400.0,
            time_units='days since 1950-01-01', calendar='360_day')
        self.dreq2 = get_or_create(DataRequest, project=proj,
            institute=institute, climate_model=climate_model,
            experiment=experiment, variable_request=var2, rip_code='r1i1p1f1',
            request_start_time=0.0, request_end_time=23400.0,
            time_units='days since 1950-01-01', calendar='360_day')
        self.user = get_or_create(User,
                                  username=Settings.get_solo().contact_user_id)
        dsub = get_or_create(DataSubmission, status=STATUS_VALUES['VALIDATED'],
            incoming_directory=incoming_directory,
            directory=incoming_directory, user=self.user)
        df1 = get_or_create( DataFile, name='file_one.nc',
            incoming_directory=incoming_directory, directory=None, size=1,
            project=proj, climate_model=climate_model, experiment=experiment,
            institute=institute, variable_request=var1, data_request=self.dreq1,
            frequency=FREQUENCY_VALUES['ann'], activity_id=act_id,
            rip_code='r1i1p1f1', online=False, start_time=0., end_time=359.,
            time_units='days since 1950-01-01', calendar=CALENDARS['360_day'],
            grid='gn', version='v12345678', tape_url='et:1234',
            data_submission=dsub)
        df2 = get_or_create( DataFile, name='file_two.nc',
            incoming_directory=incoming_directory, directory=None, size=1,
            project=proj, climate_model=climate_model, experiment=experiment,
            institute=institute, variable_request=var2, data_request=self.dreq2,
            frequency=FREQUENCY_VALUES['ann'], activity_id=act_id,
            rip_code='r1i1p1f1', online=False, start_time=0., end_time=359.,
            time_units='days since 1950-01-01', calendar=CALENDARS['360_day'],
            grid='gn', version='v12345678', tape_url='et:5678',
            data_submission=dsub)
        df3 = get_or_create( DataFile, name='file_three.nc',
            incoming_directory=incoming_directory, directory=None, size=1,
            project=proj, climate_model=climate_model, experiment=experiment,
            institute=institute, variable_request=var2, data_request=self.dreq2,
            frequency=FREQUENCY_VALUES['ann'], activity_id=act_id,
            rip_code='r1i1p1f1', online=False, start_time=360., end_time=719.,
            time_units='days since 1950-01-01', calendar=CALENDARS['360_day'],
            grid='gn', version='v12345678', tape_url='et:8765',
            data_submission=dsub)

    def test_one_file(self):
        self.assertEqual(3, DataFile.objects.count())

        one_file = DataFile.objects.filter(name='file_one.nc')

        replace_files(one_file)
        self.assertEqual(2, DataFile.objects.count())
        self.assertEqual(1, ReplacedFile.objects.count())

    def test_all_files(self):
        self.assertEqual(3, DataFile.objects.count())

        one_file = DataFile.objects.all()

        replace_files(one_file)
        self.assertEqual(0, DataFile.objects.count())
        self.assertEqual(3, ReplacedFile.objects.count())

    def test_metadata_item_copied(self):
        one_file = DataFile.objects.filter(name='file_one.nc')
        replace_files(one_file)
        old_file = ReplacedFile.objects.get(name='file_one.nc')
        self.assertEqual('et:1234', old_file.tape_url)

    def test_incoming_directory_copied(self):
        one_file = DataFile.objects.filter(name='file_one.nc')
        replace_files(one_file)
        old_file = ReplacedFile.objects.get(name='file_one.nc')
        self.assertEqual('/gws/MOHC/MY-MODEL/incoming/v12345678',
                         old_file.incoming_directory)

    def test_metadata_foreign_key_copied(self):
        one_file = DataFile.objects.filter(name='file_one.nc')
        replace_files(one_file)
        old_file = ReplacedFile.objects.get(name='file_one.nc')
        self.assertEqual('MY-MODEL', old_file.climate_model.short_name)

    def test_other_models_not_moved(self):
        climate_model = ClimateModel.objects.first()
        self.assertRaises(TypeError, replace_files, climate_model)

    def test_checksum_copied(self):
        first_file = DataFile.objects.get(name='file_one.nc')
        checksum = Checksum.objects.create(checksum_value='1234',
                                           checksum_type='ADLER32',
                                           data_file=first_file)

        one_file = DataFile.objects.filter(name='file_one.nc')
        replace_files(one_file)

        old_file = ReplacedFile.objects.get(name='file_one.nc')
        self.assertEqual('1234', old_file.checksum_value)
