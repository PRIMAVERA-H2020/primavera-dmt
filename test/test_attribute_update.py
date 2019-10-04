"""
test_attribute_update.py

Test of pdata_app/utils/attribute_update.py
"""
try:
    from unittest import mock
except ImportError:
    import mock

import django
django.setup()

from django.test import TestCase

from pdata_app.models import Checksum, DataFile
from pdata_app.tests.common import make_example_files

from pdata_app.utils.attribute_update import (SourceIdUpdate,
                                              VariantLabelUpdate,
                                              VarNameToOutNameUpdate,
                                              FileOfflineError,
                                              FileNotOnDiskError)
import pdata_app.utils.attribute_update


class TestSourceIdUpdate(TestCase):
    """Test scripts.attribute_update.SourceIdUpdate"""
    def setUp(self):
        make_example_files(self)
        self.test_file = DataFile.objects.get(name='test1')
        _make_files_realistic()
        self.test_file.refresh_from_db()
        self.desired_source_id = 'better-model'

        mock.patch.object(pdata_app.utils.attribute_update, 'BASE_OUTPUT_DIR',
                          return_value = '/gws/nopw/j04/primavera5/stream1')

        patch = mock.patch('pdata_app.utils.common.run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    def test_exit_if_no_dreq(self):
        self.dreq3.delete()
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        self.assertRaises(Exception, updater.update)

    def test_online(self):
        self.test_file.online = False
        self.test_file.save()
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        self.assertRaises(FileOfflineError, updater.update)

    def test_not_on_disk(self):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        self.assertRaises(FileNotOnDiskError, updater.update)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_source_id_updated(self, mock_checksum, mock_rename,
                               mock_available):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        self.test_file.refresh_from_db()
        self.assertEqual(self.test_file.climate_model.short_name,
                         self.desired_source_id)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_filename_updated(self, mock_checksum, mock_rename,
                              mock_available):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        self.test_file.refresh_from_db()
        desired_filename = 'var1_Amon_better-model_t_r1i1p1_gn_1950-1960.nc'
        self.assertEqual(self.test_file.name, desired_filename)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_directory_updated(self, mock_checksum, mock_rename,
                               mock_available):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        self.test_file.refresh_from_db()
        desired_dir = ('/gws/nopw/j04/primavera9/stream1/t/'
                       'HighResMIP/MOHC/better-model/t/r1i1p1/Amon/var1/gn/'
                       'v12345678')
        self.assertEqual(self.test_file.directory, desired_dir)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_update_attributes(self, mock_checksum, mock_rename,
                               mock_available):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        calls = [
            mock.call("ncatted -a source_id,global,o,c,'better-model' "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a further_info_url,global,o,c,"
                      "'https://furtherinfo.es-doc.org/t.MOHC.better-model."
                      "t.none.r1i1p1' "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
        ]
        self.mock_run_cmd.assert_has_calls(calls)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DataRequestUpdate.'
                '_update_database_attribute')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_update_file_only(self, mock_checksum, mock_rename, mock_db_change,
                              mock_available):
        updater = SourceIdUpdate(self.test_file, self.desired_source_id, True)
        updater.update()
        calls = [
            mock.call("ncatted -a source_id,global,o,c,'better-model' "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a further_info_url,global,o,c,"
                      "'https://furtherinfo.es-doc.org/t.MOHC.better-model."
                      "t.none.r1i1p1' "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
        ]
        self.mock_run_cmd.assert_has_calls(calls)
        mock_db_change.assert_not_called()

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_move_dreq(self, mock_checksum, mock_rename, mock_available):
        df = DataFile.objects.get(name='var1_table_model_expt_varlab_gn_1-2.nc')
        self.assertEqual(df.data_request.climate_model.short_name, 't')
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        df.refresh_from_db()
        self.assertEqual(df.data_request.climate_model.short_name,
                         'better-model')

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.adler32')
    @mock.patch('pdata_app.utils.attribute_update.os.path.getsize')
    def test_checksum(self, mock_size, mock_adler, mock_rename,
                      mock_available):
        mock_size.return_value = 256
        mock_adler.return_value = '9876543210'
        df = DataFile.objects.get(name='var1_table_model_expt_varlab_gn_1-2.nc')
        self.assertEqual(df.data_request.climate_model.short_name, 't')
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        df.refresh_from_db()
        self.assertEqual(df.size, 256)
        self.assertEqual(df.tape_size, 1)
        self.assertEqual(df.checksum_set.first().checksum_value, '9876543210')
        self.assertEqual(df.tapechecksum_set.first().checksum_value,
                         '1234567890')

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    @mock.patch('pdata_app.utils.attribute_update.os.makedirs')
    @mock.patch('pdata_app.utils.attribute_update.os.rename')
    @mock.patch('pdata_app.utils.attribute_update.os.listdir')
    @mock.patch('pdata_app.utils.attribute_update.delete_drs_dir')
    @mock.patch('pdata_app.utils.attribute_update.os.symlink')
    @mock.patch('pdata_app.utils.attribute_update.os.path.lexists')
    @mock.patch('pdata_app.utils.attribute_update.os.path.islink')
    @mock.patch('pdata_app.utils.attribute_update.os.remove')
    def test_renaming(self, mock_rm, mock_islink, mock_lexists, mock_symlink,
                      mock_del_drs_dir, mock_ls, mock_rename, mock_mkdirs,
                      mock_checksum, mock_available):
        mock_islink.return_vale = True
        mock_lexists.return_vale = True
        mock_ls.return_value = False
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        mock_mkdirs.assert_has_calls([
            mock.call('/gws/nopw/j04/primavera9/stream1/t/HighResMIP/MOHC/'
                      'better-model/t/r1i1p1/Amon/var1/gn/v12345678'),
            mock.call('/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/'
                      'better-model/t/r1i1p1/Amon/var1/gn/v12345678')
        ])
        mock_rename.assert_called_with(
            '/gws/nopw/j04/primavera9/stream1/path/'
            'var1_table_model_expt_varlab_gn_1-2.nc',
            '/gws/nopw/j04/primavera9/stream1/t/HighResMIP/MOHC/better-model/'
            't/r1i1p1/Amon/var1/gn/v12345678/'
            'var1_Amon_better-model_t_r1i1p1_gn_1950-1960.nc'
        )

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    @mock.patch('pdata_app.utils.attribute_update.os.makedirs')
    @mock.patch('pdata_app.utils.attribute_update.os.rename')
    @mock.patch('pdata_app.utils.attribute_update.os.listdir')
    @mock.patch('pdata_app.utils.attribute_update.delete_drs_dir')
    @mock.patch('pdata_app.utils.attribute_update.os.symlink')
    @mock.patch('pdata_app.utils.attribute_update.os.path.lexists')
    @mock.patch('pdata_app.utils.attribute_update.os.path.islink')
    @mock.patch('pdata_app.utils.attribute_update.os.remove')
    def test_sym_link(self, mock_rm, mock_islink, mock_lexists, mock_symlink,
                      mock_del_drs_dir, mock_ls, mock_rename, mock_mkdirs,
                      mock_checksum, mock_available):
        mock_islink.return_vale = True
        mock_lexists.return_vale = True
        mock_ls.return_value = False
        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        mock_rm.assert_called_once_with(
            '/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/t/t/r1i1p1/'
            'Amon/var1/gn/v12345678/var1_table_model_expt_varlab_gn_1-2.nc'
        )
        mock_mkdirs.assert_has_calls([
            mock.call('/gws/nopw/j04/primavera9/stream1/t/HighResMIP/MOHC/'
                      'better-model/t/r1i1p1/Amon/var1/gn/v12345678'),
            mock.call('/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/'
                      'better-model/t/r1i1p1/Amon/var1/gn/v12345678')
        ])
        mock_symlink.assert_called_with(
            '/gws/nopw/j04/primavera9/stream1/t/HighResMIP/MOHC/better-model/'
            't/r1i1p1/Amon/var1/gn/v12345678/'
            'var1_Amon_better-model_t_r1i1p1_gn_1950-1960.nc',
            '/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/better-model/'
            't/r1i1p1/Amon/var1/gn/v12345678/'
            'var1_Amon_better-model_t_r1i1p1_gn_1950-1960.nc'

        )

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    @mock.patch('pdata_app.utils.attribute_update.os.makedirs')
    @mock.patch('pdata_app.utils.attribute_update.os.rename')
    @mock.patch('pdata_app.utils.attribute_update.os.listdir')
    @mock.patch('pdata_app.utils.attribute_update.delete_drs_dir')
    @mock.patch('pdata_app.utils.attribute_update.os.symlink')
    @mock.patch('pdata_app.utils.attribute_update.os.path.lexists')
    @mock.patch('pdata_app.utils.attribute_update.os.path.islink')
    @mock.patch('pdata_app.utils.attribute_update.os.remove')
    def test_sym_link_not_required(self, mock_rm, mock_islink, mock_lexists,
                                   mock_symlink, mock_del_drs_dir, mock_ls,
                                   mock_rename, mock_mkdirs, mock_checksum,
                                   mock_available):
        mock_islink.return_vale = True
        mock_lexists.return_vale = True
        mock_ls.return_value = False

        self.test_file.directory = '/gws/nopw/j04/primavera5/stream1/path'
        self.test_file.save()

        updater = SourceIdUpdate(self.test_file, self.desired_source_id)
        updater.update()
        mock_mkdirs.assert_called_once_with(
            '/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/better-model/'
            't/r1i1p1/Amon/var1/gn/v12345678'
        )
        mock_rename.assert_called_with(
            '/gws/nopw/j04/primavera5/stream1/path/'
            'var1_table_model_expt_varlab_gn_1-2.nc',
            '/gws/nopw/j04/primavera5/stream1/t/HighResMIP/MOHC/better-model/'
            't/r1i1p1/Amon/var1/gn/v12345678/'
            'var1_Amon_better-model_t_r1i1p1_gn_1950-1960.nc'
        )
        mock_symlink.assert_not_called()


class TestVariantLabelUpdate(TestCase):
    """Test scripts.attribute_update.VariantLabelUpdate"""
    def setUp(self):
        make_example_files(self)
        self.test_file = DataFile.objects.get(name='test1')
        _make_files_realistic()
        self.test_file.refresh_from_db()
        self.desired_variant_label = 'r1i2p3f4'

        patch = mock.patch('pdata_app.utils.common.run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_variant_label_updated(self, mock_checksum, mock_rename,
                                   mock_available):
        updater = VariantLabelUpdate(self.test_file, self.desired_variant_label)
        updater.update()
        self.test_file.refresh_from_db()
        self.assertEqual(self.test_file.rip_code, self.desired_variant_label)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_filename_updated(self, mock_checksum, mock_rename,
                              mock_available):
        updater = VariantLabelUpdate(self.test_file, self.desired_variant_label)
        updater.update()
        self.test_file.refresh_from_db()
        desired_filename = 'var1_Amon_t_t_r1i2p3f4_gn_1950-1960.nc'
        self.assertEqual(self.test_file.name, desired_filename)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_directory_updated(self, mock_checksum, mock_rename,
                               mock_available):
        updater = VariantLabelUpdate(self.test_file, self.desired_variant_label)
        updater.update()
        self.test_file.refresh_from_db()
        desired_dir = ('/gws/nopw/j04/primavera9/stream1/t/'
                       'HighResMIP/MOHC/t/t/r1i2p3f4/Amon/var1/gn/v12345678')
        self.assertEqual(self.test_file.directory, desired_dir)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_move_dreq(self, mock_checksum, mock_rename,
                       mock_available):
        df = DataFile.objects.get(name='var1_table_model_expt_varlab_gn_1-2.nc')
        self.assertEqual(df.data_request.rip_code, 'r1i1p1f1')
        updater = VariantLabelUpdate(self.test_file, self.desired_variant_label)
        updater.update()
        df.refresh_from_db()
        self.assertEqual(df.data_request.rip_code, 'r1i2p3f4')

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_update_attributes(self, mock_checksum, mock_rename,
                               mock_available):
        updater = VariantLabelUpdate(self.test_file, self.desired_variant_label)
        updater.update()
        calls = [
            mock.call("ncatted -a variant_label,global,o,c,'r1i2p3f4' "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a realization_index,global,o,s,1 "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a initialization_index,global,o,s,2 "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a physics_index,global,o,s,3 "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a forcing_index,global,o,s,4 "
                      "/gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
            mock.call("ncatted -a further_info_url,global,o,c,"
                      "'https://furtherinfo.es-doc.org/t.MOHC.t.t.none."
                      "r1i2p3f4' /gws/nopw/j04/primavera9/stream1/path/"
                      "var1_table_model_expt_varlab_gn_1-2.nc"),
        ]
        self.mock_run_cmd.assert_has_calls(calls)


class TestVarNameToOutNameUpdate(TestCase):
    """Test scripts.attribute_update.VarNameToOutNameUpdate"""
    def setUp(self):
        make_example_files(self)
        self.test_file = DataFile.objects.get(name='test1')
        _make_files_realistic()
        self.test_file.refresh_from_db()
        var_req = self.test_file.variable_request
        var_req.out_name = 'var'
        var_req.save()

        patch = mock.patch('pdata_app.utils.common.run_command')
        self.mock_run_cmd = patch.start()
        self.addCleanup(patch.stop)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_filename_updated(self, mock_checksum, mock_rename,
                              mock_available):
        updater = VarNameToOutNameUpdate(self.test_file)
        updater.update()
        self.test_file.refresh_from_db()
        desired_filename = 'var_Amon_t_t_r1i1p1_gn_1950-1960.nc'
        self.assertEqual(self.test_file.name, desired_filename)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_directory_updated(self, mock_checksum, mock_rename,
                               mock_available):
        updater = VarNameToOutNameUpdate(self.test_file)
        updater.update()
        self.test_file.refresh_from_db()
        desired_dir = ('/gws/nopw/j04/primavera9/stream1/t/'
                       'HighResMIP/MOHC/t/t/r1i1p1/Amon/var/gn/v12345678')
        self.assertEqual(self.test_file.directory, desired_dir)

    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._check_available')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._rename_file')
    @mock.patch('pdata_app.utils.attribute_update.DmtUpdate._update_checksum')
    def test_update_attributes(self, mock_checksum, mock_rename,
                               mock_available):
        updater = VarNameToOutNameUpdate(self.test_file)
        updater.update()
        self.mock_run_cmd.assert_called_once_with(
            "ncrename -h -v var1,var "
            "/gws/nopw/j04/primavera9/stream1/path/"
            "var1_table_model_expt_varlab_gn_1-2.nc"
        )


def _make_files_realistic():
    """
    Update the files in the database created by make_example_files() to make
    them realistic enough to run these tests.
    """
    datafile = DataFile.objects.get(name='test1')
    datafile.name = 'var1_table_model_expt_varlab_gn_1-2.nc'
    datafile.incoming_name = datafile.name
    datafile.directory = '/gws/nopw/j04/primavera9/stream1/path'
    datafile.save()
    Checksum.objects.create(data_file=datafile, checksum_value='1234567890',
                            checksum_type='ADLER32')
