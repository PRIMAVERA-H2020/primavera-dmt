"""
test_validate_data_submission.py - unit tests for retrieve_request.py
"""
from __future__ import unicode_literals, division, absolute_import
import datetime
import mock

import django
django.setup()

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import make_aware

from pdata_app.utils.dbapi import get_or_create, match_one
from pdata_app.models import (Project, Institute, ClimateModel, ActivityId,
                              Experiment, VariableRequest, DataRequest,
                              RetrievalRequest, DataFile, DataSubmission,
                              Settings)
from vocabs.vocabs import (CALENDARS, FREQUENCY_VALUES, STATUS_VALUES,
                           VARIABLE_TYPES)

from scripts.retrieve_request import main, get_tape_url

class TestIntegrationTests(TestCase):
    """Integration tests run through the unittest framework and mock"""
    def setUp(self):
        # mock any external calls
        patch = mock.patch('scripts.retrieve_request._run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.rename')
        self.mock_rename = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.mkdir')
        self.mock_mkdir = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.makedirs')
        self.mock_makedirs = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.path.exists')
        self.mock_exists = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.symlink')
        self.mock_symlink = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.logger')
        self.mock_logger = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request._email_user_success')
        self.mock_email = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.os.remove')
        self.mock_remove = patch.start()
        self.addCleanup(patch.stop)

        patch = mock.patch('scripts.retrieve_request.shutil.rmtree')
        self.mock_rmtree = patch.start()
        self.addCleanup(patch.stop)

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
        self.df1 = df1
        df2 = get_or_create( DataFile, name='file_two.nc',
            incoming_directory=incoming_directory, directory=None, size=1,
            project=proj, climate_model=climate_model, experiment=experiment,
            institute=institute, variable_request=var2, data_request=self.dreq2,
            frequency=FREQUENCY_VALUES['ann'], activity_id=act_id,
            rip_code='r1i1p1f1', online=False, start_time=0., end_time=359.,
            time_units='days since 1950-01-01', calendar=CALENDARS['360_day'],
            grid='gn', version='v12345678', tape_url='et:5678',
            data_submission=dsub)
        self.df2 = df2
        df3 = get_or_create( DataFile, name='file_three.nc',
            incoming_directory=incoming_directory, directory=None, size=1,
            project=proj, climate_model=climate_model, experiment=experiment,
            institute=institute, variable_request=var2, data_request=self.dreq2,
            frequency=FREQUENCY_VALUES['ann'], activity_id=act_id,
            rip_code='r1i1p1f1', online=False, start_time=360., end_time=719.,
            time_units='days since 1950-01-01', calendar=CALENDARS['360_day'],
            grid='gn', version='v12345678', tape_url='et:8765',
            data_submission=dsub)
        self.df3 = df3

    def test_simplest(self):
        ret_req = get_or_create(RetrievalRequest, requester=self.user,
                                start_year=1000, end_year=3000, id=999999)
        ret_req.data_request.add(self.dreq1)
        ret_req.save()

        class ArgparseNamespace(object):
            retrieval_id = ret_req.id
            no_restore = False
            skip_checksums = True
            alternative = None

        self.mock_exists.side_effect = [
            False,  # if os.path.exists(retrieval_dir):
            True,  # if not os.path.exists(extracted_file_path):
            True,  # if not os.path.exists(drs_dir):
            False  # if os.path.exists(dest_file_path):
        ]

        ns = ArgparseNamespace()
        get_tape_url('et:1234', [self.df1], ns)

        df = match_one(DataFile, name='file_one.nc')
        self.assertIsNotNone(df)

        self.mock_rename.assert_called_once_with(
            '/group_workspaces/jasmin2/primavera5/.et_retrievals/ret_999999/'
            'batch_01234/gws/MOHC/MY-MODEL/incoming/v12345678/file_one.nc',
            '/group_workspaces/jasmin2/primavera5/stream1/CMIP6/HighResMIP/'
            'MOHC/MY-MODEL/experiment/r1i1p1f1/my-table/my-var/gn/v12345678/'
            'file_one.nc'
        )

        self.assertTrue(df.online)
        self.assertEqual(df.directory, '/group_workspaces/jasmin2/primavera5/'
                                       'stream1/CMIP6/HighResMIP/MOHC/'
                                       'MY-MODEL/experiment/r1i1p1f1/'
                                       'my-table/my-var/gn/v12345678')

    def test_multiple_tapes(self):
        ret_req = get_or_create(RetrievalRequest, requester=self.user,
                                start_year=1000, end_year=3000)
        ret_req.data_request.add(self.dreq1, self.dreq2)
        ret_req.save()

        class ArgparseNamespace(object):
            retrieval_id = ret_req.id
            no_restore = False
            skip_checksums = True
            alternative = None

        self.mock_exists.side_effect = [
            # first tape_url
            False,  # if os.path.exists(retrieval_dir):
            True,  # if not os.path.exists(extracted_file_path):
            True,  # if not os.path.exists(drs_dir):
            False,  # if os.path.exists(dest_file_path):
            # second tape_url
            False,  # if os.path.exists(retrieval_dir):
            True,   # if not os.path.exists(extracted_file_path):
            True,   # if not os.path.exists(drs_dir):
            False,  # if os.path.exists(dest_file_path):
            # third tape_url
            False,  # if os.path.exists(retrieval_dir):
            True,  # if not os.path.exists(extracted_file_path):
            True,  # if not os.path.exists(drs_dir):
            False  # if os.path.exists(dest_file_path):
        ]

        ns = ArgparseNamespace()
        get_tape_url('et:1234', [self.df1], ns)
        get_tape_url('et:5678', [self.df2], ns)
        get_tape_url('et:8765', [self.df3], ns)

        self.assertEqual(self.mock_rename.call_count, 3)

        for data_file in DataFile.objects.all():
            self.assertTrue(data_file.online)
            self.assertIn(data_file.directory, [
                '/group_workspaces/jasmin2/primavera5/stream1/CMIP6/'
                'HighResMIP/MOHC/MY-MODEL/experiment/r1i1p1f1/my-table/'
                'my-var/gn/v12345678',
                '/group_workspaces/jasmin2/primavera5/stream1/CMIP6/HighResMIP/'
                'MOHC/MY-MODEL/experiment/r1i1p1f1/your-table/your-var/'
                'gn/v12345678'
            ])

    def test_bad_retrieval_id(self):
        # check that the  retrieval request id doesn't exist
        ret_req_id = 1000000
        if RetrievalRequest.objects.filter(id=ret_req_id):
            raise ValueError('retrieval id already exsists')

        class ArgparseNamespace(object):
            retrieval_id = ret_req_id
            no_restore = False
            skip_checksums = True
            alternative = None

        ns = ArgparseNamespace()

        self.assertRaises(SystemExit, main, ns)
        self.mock_logger.error.assert_called_with('Unable to find retrieval id '
                                                  '{}'.format(ret_req_id))

    def test_retrieval_already_complete(self):
        completion_time = datetime.datetime(2017, 10, 31, 23, 59, 59)
        completion_time = make_aware(completion_time)

        ret_req = get_or_create(RetrievalRequest, requester=self.user,
                                date_complete=completion_time, start_year=1000,
                                end_year=3000)

        class ArgparseNamespace(object):
            retrieval_id = ret_req.id
            no_restore = False
            skip_checksums = True
            alternative = None

        ns = ArgparseNamespace()
        self.assertRaises(SystemExit, main, ns)
        self.mock_logger.error.assert_called_with('Retrieval {} was already '
                                                  'completed, at {}.'.format(
            ret_req.id, completion_time.strftime('%Y-%m-%d %H:%M')))

    def test_alternative_dir(self):
        ret_req = get_or_create(RetrievalRequest, requester=self.user,
                                start_year=1000, end_year=3000, id=999999)
        ret_req.data_request.add(self.dreq1)
        ret_req.save()

        class ArgparseNamespace(object):
            retrieval_id = ret_req.id
            no_restore = False
            skip_checksums = True
            alternative = '/group_workspaces/jasmin2/primavera3/spare_dir'

        self.mock_exists.side_effect = [
            False,  # if os.path.exists(retrieval_dir):
            True,  # if not os.path.exists(extracted_file_path):
            True,  # if not os.path.exists(drs_dir):
            False,  # if os.path.exists(dest_file_path):
            True  # if not os.path.exists(primary_path):
        ]

        ns = ArgparseNamespace()
        get_tape_url('et:1234', [self.df1], ns)

        self.mock_rename.assert_called_once_with(
            '/group_workspaces/jasmin2/primavera3/.et_retrievals/ret_999999/'
            'batch_01234/gws/MOHC/MY-MODEL/incoming/v12345678/file_one.nc',
            '/group_workspaces/jasmin2/primavera3/spare_dir/CMIP6/HighResMIP/'
            'MOHC/MY-MODEL/experiment/r1i1p1f1/my-table/my-var/gn/'
            'v12345678/file_one.nc'
        )

        self.mock_symlink.assert_called_once_with(
            '/group_workspaces/jasmin2/primavera3/spare_dir/CMIP6/HighResMIP/'
            'MOHC/MY-MODEL/experiment/r1i1p1f1/my-table/my-var/gn/'
            'v12345678/file_one.nc',
            '/group_workspaces/jasmin2/primavera5/stream1/CMIP6/HighResMIP/'
            'MOHC/MY-MODEL/experiment/r1i1p1f1/my-table/my-var/gn/v12345678/'
            'file_one.nc'
        )
