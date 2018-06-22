"""
test_common.py - unit tests for pdata_app.utils.common.py
"""
from __future__ import unicode_literals, division, absolute_import
import six

from iris.time import PartialDateTime
from numpy.testing import assert_almost_equal

from django.contrib.auth.models import User
from django.test import TestCase

from pdata_app import models
from pdata_app.utils.common import (make_partial_date_time,
                                    standardise_time_unit,
                                    calc_last_day_in_month, pdt2num,
                                    is_same_gws, get_request_size)
from pdata_app.utils import dbapi
from vocabs.vocabs import STATUS_VALUES, FREQUENCY_VALUES, VARIABLE_TYPES


class TestMakePartialDateTime(TestCase):
    def test_yyyymm(self):
        expected = PartialDateTime(year=2014, month=8)
        actual = make_partial_date_time('201408')
        self.assertEqual(actual, expected)

    def test_yyyymmdd(self):
        expected = PartialDateTime(year=2014, month=8, day=1)
        actual = make_partial_date_time('20140801')
        self.assertEqual(actual, expected)

    def test_yyyy(self):
        self.assertRaises(ValueError, make_partial_date_time, '2014')


class TestCalcLastDayInMonth(TestCase):
    def test_31_days(self):
        actual = calc_last_day_in_month(2016, 10, calendar='gregorian')

        self.assertEqual(actual, 31)

    def test_30_days(self):
        actual = calc_last_day_in_month(2016, 10, calendar='360_day')

        self.assertEqual(actual, 30)

    def test_360_day_february(self):
        actual = calc_last_day_in_month(2016, 2, calendar='360_day')

        self.assertEqual(actual, 30)

    def test_gregorian_february(self):
        actual = calc_last_day_in_month(2015, 2, calendar='gregorian')

        self.assertEqual(actual, 28)

    def test_gregorian_leap_year(self):
        actual = calc_last_day_in_month(2016, 2, calendar='gregorian')

        self.assertEqual(actual, 29)

    def test_360_day_december(self):
        actual = calc_last_day_in_month(2016, 12, calendar='360_day')

        self.assertEqual(actual, 30)

    def test_gregorian_december(self):
        actual = calc_last_day_in_month(2016, 12, calendar='gregorian')

        self.assertEqual(actual, 31)


class TestPdt2Num(TestCase):
    def test_year_month_day(self):
        pdt = PartialDateTime(2016, 8, 22)
        actual = pdt2num(pdt, 'days since 2016-08-20', 'gregorian')

        expected = 2.

        self.assertEqual(actual, expected)

    def test_year_month(self):
        pdt = PartialDateTime(2016, 8)
        actual = pdt2num(pdt, 'days since 2016-08-20', 'gregorian')

        expected = -19.

        self.assertEqual(actual, expected)

    def test_year_month_end_period(self):
        pdt = PartialDateTime(2016, 8)
        actual = pdt2num(pdt, 'days since 2016-08-20', 'gregorian',
                         start_of_period=False)

        expected = 11.

        self.assertEqual(actual, expected)

    def test_year_month_end_period_360_day(self):
        pdt = PartialDateTime(2016, 8)
        actual = pdt2num(pdt, 'days since 2016-08-20', '360_day',
                         start_of_period=False)

        expected = 10.

        self.assertEqual(actual, expected)

    def test_date_time(self):
        pdt = PartialDateTime(2016, 8, 22, 14, 42, 11)
        actual = pdt2num(pdt, 'days since 2016-08-20', 'gregorian')

        expected = 2.6126273148148148

        assert_almost_equal(actual, expected)

    def test_year(self):
        pdt = PartialDateTime(2016)
        self.assertRaises(ValueError, pdt2num, pdt, 'days since 2016-08-20',
            'gregorian')


class TestStandardiseTimeUnit(TestCase):
    """
    Test _standardise_time_unit()
    """
    def test_same_units(self):
        time_unit = 'days since 2000-01-01'
        time_num = 3.14159

        actual = standardise_time_unit(time_num, time_unit, time_unit, '360_day')
        assert_almost_equal(actual, time_num)

    def test_different_units(self):
        old_unit = 'days since 2000-01-01'
        new_unit = 'days since 2000-02-01'
        time_num = 33.14159

        actual = standardise_time_unit(time_num, old_unit, new_unit, '360_day')
        expected = 3.14159
        assert_almost_equal(actual, expected, decimal=5)

    def test_none(self):
        time_unit = 'days since 2000-01-01'
        self.assertIsNone(standardise_time_unit(None, time_unit,
                                                time_unit, '360_day'))


class TestIsSameGws(TestCase):
    def test_same(self):
        path1 = '/group_workspaces/jasmin2/primavera1/some/dir'
        path2 = '/group_workspaces/jasmin2/primavera1/another/dir'

        self.assertTrue(is_same_gws(path1, path2))

    def test_diff(self):
        path1 = '/group_workspaces/jasmin2/primavera1/some/dir'
        path2 = '/group_workspaces/jasmin2/primavera2/some/dir'

        self.assertFalse(is_same_gws(path1, path2))

    def test_bad_path(self):
        path1 = 'primavera1/some/dir'
        path2 = '/group_workspaces/jasmin2/primavera2/some/dir'

        six.assertRaisesRegex(RuntimeError, 'Cannot determine group '
            'workspace name from primavera1/some/dir', is_same_gws,
                                path1, path2)

    def test_slightly_bad_path(self):
        path1 = '/group_workspaces/jasmin2/primavera2/some/dir'
        path2 = '/group_workspaces/jasmin1/primavera1/some/dir'

        six.assertRaisesRegex(RuntimeError, 'Cannot determine group '
            'workspace name from /group_workspaces/jasmin1/primavera1/some/dir',
                                is_same_gws, path1, path2)


class TestGetRequestSize(TestCase):
    def setUp(self):
        project = dbapi.get_or_create(models.Project, short_name='t',
                                      full_name='test')
        clim_mod = dbapi.get_or_create(models.ClimateModel, short_name='t',
                                       full_name='test')
        institute = dbapi.get_or_create(models.Institute, short_name='MOHC',
                                        full_name='Met Office Hadley Centre')
        expt = dbapi.get_or_create(models.Experiment, short_name='t',
                                   full_name='test')
        vble1 = dbapi.get_or_create(models.VariableRequest,
                                   table_name='Amon',
                                   long_name='very descriptive', units='1',
                                   var_name='var1',
                                   standard_name='var_name',
                                   cell_methods='time:mean',
                                   positive='optimistic',
                                   variable_type=VARIABLE_TYPES['real'],
                                   dimensions='massive', cmor_name='var1',
                                   modeling_realm='atmos',
                                   frequency=FREQUENCY_VALUES['ann'],
                                   cell_measures='', uid='123abc')
        vble2 = dbapi.get_or_create(models.VariableRequest,
                                   table_name='Amon',
                                   long_name='very descriptive', units='1',
                                   var_name='var2',
                                   standard_name='var_name',
                                   cell_methods='time:mean',
                                   positive='optimistic',
                                   variable_type=VARIABLE_TYPES['real'],
                                   dimensions='massive', cmor_name='var1',
                                   modeling_realm='atmos',
                                   frequency=FREQUENCY_VALUES['ann'],
                                   cell_measures='', uid='123abc')
        self.dreq1 = dbapi.get_or_create(models.DataRequest, project=project,
                                   institute=institute,
                                   climate_model=clim_mod, experiment=expt,
                                   variable_request=vble1,
                                   rip_code='r1i1p1f1',
                                   request_start_time=0.0,
                                   request_end_time=23400.0,
                                   time_units='days since 1950-01-01',
                                   calendar='360_day')
        self.dreq2 = dbapi.get_or_create(models.DataRequest, project=project,
                                   institute=institute,
                                   climate_model=clim_mod, experiment=expt,
                                   variable_request=vble2,
                                   rip_code='r1i1p1f1',
                                   request_start_time=0.0,
                                   request_end_time=23400.0,
                                   time_units='days since 1950-01-01',
                                   calendar='360_day')
        self.user = dbapi.get_or_create(User, username='fred')
        act_id = dbapi.get_or_create(models.ActivityId,
                                     short_name='HighResMIP',
                                     full_name='High Resolution Model Intercomparison Project')
        dsub = dbapi.get_or_create(models.DataSubmission,
                                   status=STATUS_VALUES['EXPECTED'],
                                   incoming_directory='/some/dir',
                                   directory='/some/dir', user=self.user)
        data_file1 = dbapi.get_or_create(models.DataFile, name='test1',
                                        incoming_directory='/some/dir',
                                        directory='/some/dir', size=1,
                                        project=project,
                                        climate_model=clim_mod,
                                        institute=institute,
                                        experiment=expt,
                                        variable_request=vble1,
                                        data_request=self.dreq1,
                                        activity_id=act_id, frequency='t',
                                        rip_code='r1i1p1',
                                        data_submission=dsub, online=True,
                                        start_time=0, end_time=18000,
                                        calendar='360_day',
                                        time_units='days since 1950-01-01')
        data_file2 = dbapi.get_or_create(models.DataFile, name='test2',
                                        incoming_directory='/some/dir',
                                        directory='/some/dir', size=2,
                                        project=project,
                                        climate_model=clim_mod,
                                        institute=institute,
                                        experiment=expt,
                                        variable_request=vble2,
                                        data_request=self.dreq2,
                                        activity_id=act_id, frequency='t',
                                        rip_code='r1i1p1',
                                        data_submission=dsub, online=False)

    def test_all_files(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                   requester=self.user,
                                   start_year=1950, end_year=2000)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(3, get_request_size(rreq))

    def test_dates(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=2001, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(2, get_request_size(rreq))

    def test_online(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(1, get_request_size(rreq, online=True))

    def test_offline(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(2, get_request_size(rreq, offline=True))

    def test_both_options(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertRaises(ValueError, get_request_size, rreq,
                          online= True, offline=True)

    def test_no_files(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=2001, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(0, get_request_size(rreq, online=True))
