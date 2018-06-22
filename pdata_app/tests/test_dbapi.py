"""
Unit tests for pdata_app.utils.dbapi
"""
from __future__ import unicode_literals, division, absolute_import

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from pdata_app.utils import dbapi
from pdata_app import models
from vocabs.vocabs import (STATUS_VALUES, CHECKSUM_TYPES,
    FREQUENCY_VALUES, VARIABLE_TYPES)


class TestGetOrCreate(TestCase):
    def setUp(self):
        self.cm = dbapi.get_or_create(models.ClimateModel, short_name='t',
            full_name='test')

    def test_create(self):
        self.assertEqual(models.ClimateModel.objects.count(), 1)
        self.assertEqual(self.cm.full_name, 'test')
        self.assertEqual(self.cm.short_name, 't')

    def test_get(self):
        cm2 = dbapi.get_or_create(models.ClimateModel, short_name='t',
            full_name='test')

        self.assertEqual(models.ClimateModel.objects.count(), 1)
        self.assertEqual(cm2.full_name, 'test')
        self.assertEqual(cm2.short_name, 't')


class TestExists(TestCase):
    def setUp(self):
        self.cm = dbapi.get_or_create(models.ClimateModel, short_name='t',
            full_name='test')

    def test_exists(self):
        self.assertTrue(dbapi.exists(models.ClimateModel, short_name='t',
            full_name='test'))

    def test_does_not_exist(self):
        self.assertFalse(dbapi.exists(models.ClimateModel, short_name='g',
            full_name='test'))


class TestGetChecksum(TestCase):
    def setUp(self):
        self.data_file = _create_file_object()

        _cm1 = dbapi.get_or_create(models.Checksum, data_file=self.data_file,
            checksum_value='ABCD1234', checksum_type=CHECKSUM_TYPES['MD5'])

        _cm2 = dbapi.get_or_create(models.Checksum, data_file=self.data_file,
            checksum_value='4321DCBA', checksum_type=CHECKSUM_TYPES['SHA256'])

    def test_md5(self):
        self.assertEqual(dbapi.get_checksum(self.data_file), 'ABCD1234')

    def test_sha256(self):
        self.assertEqual(dbapi.get_checksum(self.data_file,
            checksum_type='SHA256'), '4321DCBA')


class TestCount(TestCase):
    def setUp(self):
        data_file = _create_file_object()

        _cm1 = dbapi.get_or_create(models.Checksum, data_file=data_file,
            checksum_value='ABCD1234', checksum_type=CHECKSUM_TYPES['MD5'])

        _cm2 = dbapi.get_or_create(models.Checksum, data_file=data_file,
            checksum_value='4321DCBA', checksum_type=CHECKSUM_TYPES['SHA256'])

    def test_no_objects(self):
        self.assertEqual(dbapi.count(models.DataIssue), 0)

    def test_one_object(self):
        self.assertEqual(dbapi.count(models.DataFile), 1)

    def test_two_objects(self):
        self.assertEqual(dbapi.count(models.Checksum), 2)


class TestInsert(TestCase):
    def test_simple_insert(self):
        _i = dbapi.insert(models.Institute, short_name='t', full_name='test')

        self.assertEqual(models.Institute.objects.count(), 1)
        self.assertEqual(models.Institute.objects.all()[0].short_name, 't')
        self.assertEqual(models.Institute.objects.all()[0].full_name, 'test')

    def test_insert_two_objects(self):
        _i = dbapi.insert(models.Institute, short_name='t', full_name='test')
        _j = dbapi.insert(models.Institute, short_name='z', full_name='zest')

        self.assertEqual(models.Institute.objects.count(), 2)

    def test_raises_exception(self):
        _e = dbapi.insert(models.ESGFDataset, drs_id='a', version='2',
            directory='c')
        self.assertRaises(IntegrityError, dbapi.insert, models.ESGFDataset,
            drs_id='a', version='2', directory='d')


class TestMatchOne(TestCase):
    def setUp(self):
        _i = dbapi.get_or_create(models.Institute, short_name='t', full_name='test')
        _j = dbapi.get_or_create(models.Institute, short_name='s', full_name='test')

    def test_single_match(self):
        item_matched = dbapi.match_one(models.Institute, short_name='t')

        self.assertEqual(item_matched.short_name, 't')

    def test_double_match_returns_none(self):
        self.assertIsNone(dbapi.match_one(models.Institute, full_name='test'))

    def test_no_match_returns_none(self):
        self.assertIsNone(dbapi.match_one(models.Institute, full_name='real'))


class TestIsPaused(TestCase):
    def test_settings_blank(self):
        self.assertFalse(dbapi.is_paused())

    def test_set_to_false_as_default(self):
        _settings = models.Settings.get_solo()

        self.assertFalse(dbapi.is_paused())

    def test_set_true(self):
        settings = models.Settings.get_solo()
        settings.is_paused = True
        settings.save()

        self.assertTrue(dbapi.is_paused())


def _create_file_object():
    """
    Creates a file object in the database and returns the corresponding object
    """
    project = dbapi.get_or_create(models.Project, short_name='t',
        full_name='test')
    clim_mod = dbapi.get_or_create(models.ClimateModel, short_name='t',
        full_name='test')
    institute = dbapi.get_or_create(models.Institute, short_name='MOHC',
                              full_name='Met Office Hadley Centre')
    expt = dbapi.get_or_create(models.Experiment, short_name='t',
        full_name='test')
    vble = dbapi.get_or_create(models.VariableRequest, table_name='Amon',
        long_name='very descriptive', units='1', var_name='var1',
        standard_name='var_name', cell_methods='time:mean',
        positive='optimistic', variable_type=VARIABLE_TYPES['real'],
        dimensions='massive', cmor_name='var1', modeling_realm='atmos',
        frequency=FREQUENCY_VALUES['ann'], cell_measures='', uid='123abc')
    dreq = dbapi.get_or_create(models.DataRequest, project=project,
        institute=institute, climate_model=clim_mod, experiment=expt,
        variable_request=vble, rip_code='r1i1p1f1', request_start_time=0.0,
        request_end_time=23400.0, time_units='days since 1950-01-01',
        calendar='360_day')
    user = dbapi.get_or_create(User, username='fred')
    dsub = dbapi.get_or_create(models.DataSubmission,
        status=STATUS_VALUES['EXPECTED'], incoming_directory='/some/dir',
        directory='/some/dir', user=user)
    act_id = dbapi.get_or_create(models.ActivityId, short_name='HighResMIP',
        full_name='High Resolution Model Intercomparison Project')

    data_file = dbapi.get_or_create(models.DataFile, name='test',
        incoming_directory='/some/dir', directory='/some/dir', size=1,
        project=project, climate_model=clim_mod, institute=institute,
        experiment=expt, variable_request=vble, data_request= dreq,
        activity_id=act_id, frequency='t', rip_code='r1i1p1',
        data_submission=dsub, online=False)

    return data_file
