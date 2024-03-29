"""
test_common.py - unit tests for pdata_app.utils.common.py
"""
from __future__ import unicode_literals, division, absolute_import
from pathlib import Path
import shutil
import tempfile

try:
    from unittest import mock
except ImportError:
    import mock

try:
    from iris.time import PartialDateTime
except ImportError:
    from partial_date_time import PartialDateTime
from numpy.testing import assert_almost_equal

from django.test import TestCase

from pdata_app import models
from pdata_app.utils.common import (make_partial_date_time,
                                    standardise_time_unit,
                                    calc_last_day_in_month, pdt2num,
                                    list_files, ilist_files,
                                    remove_empty_dirs,
                                    is_same_gws, get_gws, get_gws_any_dir,
                                    construct_drs_path,
                                    construct_filename,
                                    construct_cylc_task_name,
                                    construct_time_string, get_request_size,
                                    date_filter_files, grouper,
                                    directories_spanned, run_ncatted,
                                    run_ncrename)
from pdata_app.utils import dbapi
from .common import make_example_files


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


class BasePathIteratorTest(TestCase):
    """
    An base class for tests that involve iterating through a directory
    structure.
    """
    def setUp(self):
        """
        Create a temporary file structure with the structure:
        .
        |-- dir1
        |   |-- dir2
        |   |   `-- dir3
        |   `-- file3.nc
        |   `-- file4.nc -> file3.nc
        |   `-- file5.pp
        |-- file1.nc
        `-- file2.pp
        """
        temp_path = tempfile.mkdtemp()
        temp_dir = Path(temp_path)
        dir1 = temp_dir.joinpath('dir1')
        dir1.mkdir()
        temp_dir.joinpath('file1.nc').touch()
        temp_dir.joinpath('file2.pp').touch()
        dir2 = dir1.joinpath('dir2')
        dir2.mkdir()
        file3 = dir1.joinpath('file3.nc')
        file3.touch()
        dir1.joinpath('file4.nc').symlink_to(file3)
        dir1.joinpath('file5.pp').touch()
        dir2.joinpath('dir3').mkdir()
        self.temp_dir = temp_dir

    def tearDown(self):
        """
        Remove the temporary file structure
        """
        shutil.rmtree(self.temp_dir)


class TestListFiles(BasePathIteratorTest):
    """
    Test list_files
    """
    def test_list_files_default_suffix(self):
        actual_tree_list = list_files(self.temp_dir)
        expected_files = [
            'file1.nc',
            'dir1/file3.nc',
            'dir1/file4.nc'
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        actual_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(actual_tree_list, expected_tree_list)

    def test_list_files_any_suffix(self):
        actual_tree_list = list_files(self.temp_dir, suffix='')
        expected_files = [
            'file1.nc',
            'file2.pp',
            'dir1/file3.nc',
            'dir1/file4.nc',
            'dir1/file5.pp'
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        actual_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(actual_tree_list, expected_tree_list)

    def test_list_files_ignore_symlinks(self):
        actual_tree_list = list_files(self.temp_dir, ignore_symlinks=True)
        expected_files = [
            'file1.nc',
            'dir1/file3.nc'
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        actual_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(actual_tree_list, expected_tree_list)


class TestIListFiles(BasePathIteratorTest):
    """
    Test ilist_files
    """
    def test_ilist_files_default_suffix(self):
        new_tree_list = list(ilist_files(self.temp_dir))
        expected_files = [
            'file1.nc',
            'dir1/file3.nc',
            'dir1/file4.nc'
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        new_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(new_tree_list, expected_tree_list)

    def test_ilist_files_any_suffix(self):
        new_tree_list = list(ilist_files(self.temp_dir, suffix=''))
        expected_files = [
            'file1.nc',
            'file2.pp',
            'dir1/file3.nc',
            'dir1/file4.nc',
            'dir1/file5.pp'
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        new_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(new_tree_list, expected_tree_list)

    def test_ilist_files_ignore_symlinks(self):
        new_tree_list = list(ilist_files(self.temp_dir, ignore_symlinks=True))
        expected_files = [
            'file1.nc',
            'dir1/file3.nc',
        ]
        expected_tree_list = [self.temp_dir.joinpath(ef).as_posix()
                              for ef in expected_files]
        new_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(new_tree_list, expected_tree_list)


class TestRemoveEmptyDirs(BasePathIteratorTest):
    """
    Test remove_empty_dirs
    """
    def test_files_deleted(self):
        remove_empty_dirs(self.temp_dir)
        new_tree_list = [
            p.relative_to(self.temp_dir).as_posix()
            for p in self.temp_dir.rglob('*')
        ]
        expected_tree_list = [
            'dir1',
            'file1.nc',
            'file2.pp',
            'dir1/file3.nc',
            'dir1/file4.nc',
            'dir1/file5.pp'
        ]
        new_tree_list.sort()
        expected_tree_list.sort()
        self.assertEqual(new_tree_list, expected_tree_list)

    @mock.patch('pdata_app.utils.common.logger')
    def test_exception(self, mock_logger):
        # remove user write permission from dir2 so that dir3 cannot be removed
        self.temp_dir.joinpath('dir1/dir2').chmod(0o555)
        remove_empty_dirs(self.temp_dir)
        dir3_path = self.temp_dir.joinpath('dir1/dir2/dir3').as_posix()
        error_message = f"[Errno 13] Permission denied: '{dir3_path}'"
        # restore permissions to allow tearDown() to run
        self.temp_dir.joinpath('dir1/dir2').chmod(0o755)
        # now it's back to normal, run assert
        mock_logger.error.assert_called_with(error_message)


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

    def test_new_same(self):
        path1 = '/gws/nopw/j04/primavera1/some/dir'
        path2 = '/gws/nopw/j04/primavera1/another/dir'

        self.assertTrue(is_same_gws(path1, path2))

    def test_new_diff(self):
        path1 = '/gws/nopw/j04/primavera1/some/dir'
        path2 = '/gws/nopw/j04/primavera5/another/dir'

        self.assertFalse(is_same_gws(path1, path2))

    def test_archive_first(self):
        path1 = '/badc/cmip6'
        path2 = '/group_workspaces/jasmin2/primavera2/some/dir'

        self.assertFalse(is_same_gws(path1, path2))

    def test_archive_second(self):
        path1 = '/group_workspaces/jasmin2/primavera2/some/dir'
        path2 = '/badc/cmip6'

        self.assertFalse(is_same_gws(path1, path2))

    def test_slightly_bad_path(self):
        path1 = '/group_workspaces/jasmin2/primavera2/some/dir'
        path2 = '/group_workspaces/jasmin1/primavera1/some/dir'

        self.assertFalse(is_same_gws(path1, path2))


class TestGetGws(TestCase):
    """Test pdata_app.utils.common.get_gws()"""
    def test_gws1(self):
        path = '/gws/nopw/j04/primavera1/stream1/drs/path/blah'

        self.assertEqual(get_gws(path),
                         '/gws/nopw/j04/primavera1/stream1')

    def test_missing_stream(self):
        path = '/gws/nopw/j04/primavera1/drs/path/blah'

        self.assertRaises(RuntimeError, get_gws, path)

    def test_anything_else(self):
        path = '/rabbits'

        self.assertRaises(RuntimeError, get_gws, path)


class TestGetGwsAnyDir(TestCase):
    """Test pdata_app.utils.common.get_gws_any_dir()"""
    def test_gws1(self):
        path = '/gws/nopw/j04/primavera1/stream1/drs/path/blah'

        self.assertEqual(get_gws_any_dir(path),
                         '/gws/nopw/j04/primavera1')

    def test_any_dir(self):
        path = '/gws/nopw/j04/primavera9/drs/path/blah'

        self.assertEqual(get_gws_any_dir(path),
                         '/gws/nopw/j04/primavera9')

    def test_anything_else(self):
        path = '/rabbits'

        self.assertRaises(RuntimeError, get_gws_any_dir, path)


class TestConstructDrsPath(TestCase):
    """Test pdata_app.utils.common.construct_drs_path()"""
    def setUp(self):
        make_example_files(self)

    def test_success(self):
        expected = 't/HighResMIP/MOHC/t/t/r1i1p1/Amon/var1/gn/v12345678'
        self.assertEqual(construct_drs_path(self.data_file1), expected)

    def test_out_name(self):
        expected = 't/HighResMIP/MOHC/t/t/r1i1p1/Amon/var/g2/v87654321'
        self.assertEqual(construct_drs_path(self.data_file2), expected)



class TestConstructFilename(TestCase):
    """Test pdata_app.utils.common.construct_filename()"""
    def setUp(self):
        make_example_files(self)
        datafile = models.DataFile.objects.get(name='test1')
        datafile.name = 'var_table_model_expt_varlab_gn_1-2.nc'
        datafile.save()

    def test_basic(self):
        datafile = models.DataFile.objects.get(
            name='var_table_model_expt_varlab_gn_1-2.nc')
        actual = construct_filename(datafile)
        expected = 'var1_Amon_t_t_r1i1p1_gn_1950-1960.nc'
        self.assertEqual(actual, expected)

    def test_no_time(self):
        datafile = models.DataFile.objects.get(
            name='var_table_model_expt_varlab_gn_1-2.nc')
        datafile.frequency = 'fx'
        datafile.save()
        actual = construct_filename(datafile)
        expected = 'var1_Amon_t_t_r1i1p1_gn.nc'
        self.assertEqual(actual, expected)

    def test_out_name(self):
        var_req = self.data_file8.variable_request
        var_req.out_name = 'short'
        var_req.save()
        expected = 'short_Amon_t_t_r1i1p1_g8_1980-1990.nc'
        self.assertEqual(construct_filename(self.data_file8), expected)



class TestConstructCylcTaskName(TestCase):
    """Test pdata_app.utils.common.construct_cylc_task_name()"""
    def setUp(self):
        make_example_files(self)

    def test_basic(self):
        actual = construct_cylc_task_name(self.esgf_dataset, 'crepp_monitor')
        expected = 'crepp_monitor_t_t_r1i1p1f1_Amon_var1'
        self.assertEqual(actual, expected)


class TestConstructTimeString(TestCase):
    """Test pdata_app.utils.common.construct_time_string()"""
    def test_yearly(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', 'ann')
        expected = '1951'
        self.assertEqual(actual, expected)

    def test_monthly(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', 'mon')
        expected = '195101'
        self.assertEqual(actual, expected)

    def test_daily(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', 'day')
        expected = '19510101'
        self.assertEqual(actual, expected)

    def test_6hourly(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', '6hr')
        expected = '195101010000'
        self.assertEqual(actual, expected)

    def test_3hourly(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', '3hr')
        expected = '195101010000'
        self.assertEqual(actual, expected)

    def test_hourly(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       '360_day', '1hr')
        expected = '195101010000'
        self.assertEqual(actual, expected)

    def test_gregorian(self):
        actual = construct_time_string(360.0, 'days since 1950-01-01',
                                       'gregorian', 'ann')
        expected = '1950'
        self.assertEqual(actual, expected)

    def test_other_freq(self):
        self.assertRaises(NotImplementedError, construct_time_string, 360.,
                          'days since 1950-01-01', '360_day', 'fx')


class TestGetRequestSize(TestCase):
    def setUp(self):
        make_example_files(self)

    def test_all_files(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                   requester=self.user,
                                   start_year=1950, end_year=2000)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(15, get_request_size(rreq.data_request.all(),
                                             rreq.start_year, rreq.end_year))

    def test_dates(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=1975)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(7, get_request_size(rreq.data_request.all(),
                                             rreq.start_year, rreq.end_year))

    def test_online(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(3, get_request_size(rreq.data_request.all(),
                         rreq.start_year, rreq.end_year, online=True))

    def test_offline(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(12, get_request_size(rreq.data_request.all(),
                                             rreq.start_year, rreq.end_year,
                                             offline=True))

    def test_both_options(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=1950, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertRaises(ValueError, get_request_size,
                          rreq.data_request.all(), rreq.start_year,
                          rreq.end_year, online= True, offline=True)

    def test_no_files(self):
        rreq = dbapi.get_or_create(models.RetrievalRequest,
                                    requester=self.user,
                                    start_year=2001, end_year=2014)
        rreq.data_request.add(self.dreq1)
        rreq.save()
        rreq.data_request.add(self.dreq2)
        rreq.save()

        self.assertEqual(0, get_request_size(rreq.data_request.all(),
                                             rreq.start_year, rreq.end_year,
                                             offline=True))

    def test_manual_list(self):
        self.assertEqual(15, get_request_size([self.dreq1, self.dreq2],
                                             1950, 2000))


class TestDateFilterFiles(TestCase):
    def setUp(self):
        make_example_files(self)

    def test_entirely_contains(self):
        data_files =  models.DataFile.objects.all()
        self.assertEqual(['test1', 'test2'],
                         _assertable(date_filter_files(data_files,
                                                       1949, 1961)))

    def test_end_spans(self):
        data_files =  models.DataFile.objects.all()
        self.assertEqual(['test1', 'test2', 'test4'],
                         _assertable(date_filter_files(data_files,
                                                       1949, 1975)))

    def test_start_spans(self):
        data_files =  models.DataFile.objects.all()
        self.assertEqual(['test2', 'test4', 'test8'],
                         _assertable(date_filter_files(data_files,
                                                       1965, 1995)))

    def test_both_span(self):
        data_files =  models.DataFile.objects.all()
        self.assertEqual(['test1', 'test2', 'test4', 'test8'],
                         _assertable(date_filter_files(data_files,
                                                       1955, 1987)))

    def test_subset_entirely(self):
        data_files =  models.DataFile.objects.filter(online=False)
        self.assertEqual(['test4', 'test8'],
                         _assertable(date_filter_files(data_files,
                                                       1952, 1992)))

    def test_subset_spans(self):
        data_files =  models.DataFile.objects.filter(online=False)
        self.assertEqual(['test4', 'test8'],
                         _assertable(date_filter_files(data_files,
                                                       1975, 1985)))


class TestGrouper(TestCase):
    def test_exact_multiple(self):
        actual = [list(chunk) for chunk in grouper(range(8), 4)]
        expected = [[0, 1, 2, 3], [4, 5, 6, 7]]
        self.assertEqual(actual, expected)

    def test_non_exact_multiple(self):
        actual = [list(chunk) for chunk in grouper(range(10), 4)]
        expected = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
        self.assertEqual(actual, expected)

    def test_n_is_one(self):
        actual = [list(chunk) for chunk in grouper(range(3), 1)]
        expected = [[0], [1], [2]]
        self.assertEqual(actual, expected)

    def test_other_type(self):
        actual = [list(chunk) for chunk in grouper(list(range(10)), 4)]
        expected = [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
        self.assertEqual(actual, expected)


class TestDirectoriesSpanned(TestCase):
    def setUp(self):
        make_example_files(self)
        self.dreq = models.DataRequest.objects.get(
            variable_request__var_name='var1',
            climate_model__short_name='t',
            rip_code='r1i1p1f1'
        )

    def test_correct_order(self):
        dirs_list = directories_spanned(self.dreq)
        expected = [
            {'dir_name': '/some/dir1', 'num_files': 1, 'dir_size': 1},
            {'dir_name': '/some/dir2', 'num_files': 2, 'dir_size': 12}
        ]
        self.assertEqual(dirs_list, expected)

    def test_wrong_order(self):
        dirs_list = directories_spanned(self.dreq)
        expected = [
            {'dir_name': '/some/dir2', 'num_files': 2, 'dir_size': 12},
            {'dir_name': '/some/dir1', 'num_files': 1, 'dir_size': 1}
        ]
        self.assertNotEqual(dirs_list, expected)


class TestRunNcatted(TestCase):
    def setUp(self):
        patch = mock.patch('pdata_app.utils.common.run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    def test_global_attr(self):
        run_ncatted('/a', 'b.nc', 'source_id', 'global', 'c', 'better-model')
        self.mock_run_cmd.assert_called_once_with(
            "ncatted -h -a source_id,global,o,c,'better-model' /a/b.nc"
        )

    def test_var_attr(self):
        run_ncatted('/a', 'b.nc', 'cell_methods', 'tas', 'c', 'better-method')
        self.mock_run_cmd.assert_called_once_with(
            "ncatted -h -a cell_methods,tas,o,c,'better-method' /a/b.nc"
        )

    def test_int(self):
        run_ncatted('/a', 'b.nc', 'source_id', 'global', 'd', 123)
        self.mock_run_cmd.assert_called_once_with(
            "ncatted -h -a source_id,global,o,d,123 /a/b.nc"
        )

    def test_with_history(self):
        run_ncatted('/a', 'b.nc', 'source_id', 'global', 'c', 'better-model',
                    suppress_history=False)
        self.mock_run_cmd.assert_called_once_with(
            "ncatted -a source_id,global,o,c,'better-model' /a/b.nc"
        )


class TestRunNcrename(TestCase):
    def setUp(self):
        patch = mock.patch('pdata_app.utils.common.run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    def test_typical(self):
        run_ncrename('/a', 'b.nc', 'abc', 'ab')
        self.mock_run_cmd.assert_called_once_with(
            "ncrename -h -v abc,ab /a/b.nc"
        )

    def test_with_history(self):
        run_ncrename('/a', 'b.nc', 'abc', 'ab', suppress_history=False)
        self.mock_run_cmd.assert_called_once_with(
            "ncrename -v abc,ab /a/b.nc"
        )


def _assertable(queryset, list_item='name'):
    """
    From a Django queryset return a list of one attribute that can be passed
    to an assert statement. The default model attribute to compare is name.

    :param django.db.models.query.QuerySet queryset:
    :returns: A list of the specified attrributes from each element of the
        queryset.
    :rtype: list
    """
    return list(queryset.order_by(list_item).values_list(list_item, flat=True))
