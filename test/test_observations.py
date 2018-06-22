"""
test_observations.py - unit tests for the observations classes
"""
from __future__ import unicode_literals, division, absolute_import
import django
django.setup()

from django.test import TestCase
from pdata_app.models import ObservationDataset, ObservationFile


class TestObservationSet(TestCase):
    """ Test the observations set object """
    def setUp(self):
        self.first_file_params = {
            'name': 'obs_day_OBS-1_1deg_197801_199912.nc',
            'incoming_directory': '/some/dir',
            'directory': '/some/dir',
            'online': True,
            'size': 1,
        }
        self.second_file_params = {
            'name': 'obs_day_OBS-1_1deg_200012_201812.nc',
            'incoming_directory': '/some/dir',
            'directory': '/some/dir',
            'online': True,
            'size': 1,
        }

    def test_obs_set_creation(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        self.assertEqual(ods.name, 'OBS')
        self.assertEqual(ods.version, '1')

    def test_add_file(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        self.assertEqual(ods.observationfile_set.count(), 1)

    def test_obs_files_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        self.assertIsInstance(ods.obs_files, django.db.models.query.QuerySet)
        self.assertEqual(ods.obs_files.count(), 1)
        self.assertIsInstance(ods.obs_files.first(), ObservationFile)
        self.assertEqual(ods.obs_files.first().name,
                         'obs_day_OBS-1_1deg_197801_199912.nc')

    def test_missing_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        self.assertIsNone(ods.variables)

    def test_one_variables_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             var_name='tas',
                                             **self.first_file_params)
        odf.save()
        self.assertEqual(ods.variables, ['tas'])

    def test_two_variables_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             var_name='tas',
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             var_name='tos',
                                             **self.second_file_params)
        odf.save()
        self.assertEqual(ods.variables, ['tas', 'tos'])

    def test_incoming_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.save()
        self.assertEqual(ods.incoming_directories, ['/some/dir'])

    def test_directories_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.directory = '/other/dir'
        odf.save()
        self.assertEqual(ods.directories, ['/other/dir', '/some/dir'])

    def test_tape_urls_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.tape_url = 'moose:/'
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.tape_url = 'et:1234'
        odf.save()
        self.assertEqual(ods.tape_urls, ['et:1234', 'moose:/'])

    def test_frequencies_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.frequency = '1hr'
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.frequency = 'mon'
        odf.save()
        self.assertEqual(ods.frequencies, ['1hr', 'mon'])

    def test_units_property(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.units = 'degree_east'
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.units = 'mol m-2 s-1 sr-1'
        odf.save()
        self.assertEqual(ods.units, ['degree_east', 'mol m-2 s-1 sr-1'])

    def test_times(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             start_time=0.0,
                                             end_time=364.99,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             start_time=365.0,
                                             end_time=729.99,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.second_file_params)
        odf.save()
        self.assertEqual(ods.start_time.strftime('%Y-%m-%d'), '1950-01-01')
        self.assertEqual(ods.end_time.strftime('%Y-%m-%d'), '1951-12-31')

    def test_status_online(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.save()
        self.assertEqual(ods.online_status, 'online')

    def test_status_partial(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.online = False
        odf.save()
        self.assertEqual(ods.online_status, 'partial')

    def test_status_offline(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.first_file_params)
        odf.online = False
        odf.save()
        odf = ObservationFile.objects.create(obs_set=ods,
                                             **self.second_file_params)
        odf.online = False
        odf.save()
        self.assertEqual(ods.online_status, 'offline')

    def test_unicode_version(self):
        ods = ObservationDataset.objects.create(name='OBS', version='1')
        self.assertEqual(str(ods), 'OBS ver 1')

    def test_unicode_no_version(self):
        ods = ObservationDataset.objects.create(name='OBS', version=None)
        self.assertEqual(str(ods), 'OBS')


class TestObservationFile(TestCase):
    """ Test the observations file object """
    def setUp(self):
        self.ods = ObservationDataset.objects.create(name='OBS', version='1')
        self.basic_file_params = {
            'name': 'obs_day_OBS-1_1deg_197801_201812.nc',
            'incoming_directory': '/some/dir',
            'directory': '/some/dir',
            'online': True,
            'size': 1,
        }

    def test_variable_standard_name(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             standard_name='cloud_albedo',
                                             long_name='wibble wobble',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.variable, 'cloud_albedo')

    def test_variable_long_name(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             long_name='wibble wobble',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.variable, 'wibble wobble')

    def test_variable_var_name(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             var_name='wobble wabble',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.variable, 'wobble wabble')

    def test_variable_not_specified(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             **self.basic_file_params)
        odf.save()
        self.assertIsNone(odf.variable)

    def test_start_string_none(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             **self.basic_file_params)
        odf.save()
        self.assertIsNone(odf.start_string)

    def test_start_string_zero(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             start_time=0.0,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.start_string, '1950-01-01')

    def test_start_string(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             start_time=364.99,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.start_string, '1950-12-31')

    def test_end_string_none(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             **self.basic_file_params)
        odf.save()
        self.assertIsNone(odf.end_string)

    def test_end_string_zero(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             end_time=0.0,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.end_string, '1950-01-01')

    def test_end_string(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             end_time=181.5,
                                             calendar='gregorian',
                                             time_units='days since 1950-01-01',
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(odf.end_string, '1950-07-01')

    def test_unicode(self):
        odf = ObservationFile.objects.create(obs_set=self.ods,
                                             **self.basic_file_params)
        odf.save()
        self.assertEqual(str(odf), 'obs_day_OBS-1_1deg_197801_201812.nc '
                                   '(Directory: /some/dir)')
