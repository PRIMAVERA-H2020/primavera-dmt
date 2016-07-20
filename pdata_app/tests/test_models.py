"""
Unit tests for pdata_app.models
"""
import os
import datetime
import pytz

from django.test import TestCase
from django.core.exceptions import ValidationError

from pdata_app import models
from vocabs import STATUS_VALUES, ONLINE_STATUS
from pdata_app.utils.dbapi import get_or_create
from test.test_datasets import test_data_submission


def _extract_file_metadata(file_path):
    """
    Extracts metadata from file name and returns dictionary.
    """
    # e.g. tasmax_day_IPSL-CM5A-LR_amip4K_r1i1p1_18590101-18591230.nc
    keys = ("var_id", "frequency", "climate_model", "experiment", "ensemble", "time_range")

    items = os.path.splitext(os.path.basename(file_path))[0].split("_")
    data = {}

    for i in range(len(items)):
        key = keys[i]
        value = items[i]

        if key == "time_range":
            start_time, end_time = value.split("-")
            data["start_time"] = datetime.datetime.strptime(start_time, "%Y%m%d")
            data["end_time"] = datetime.datetime.strptime(end_time, "%Y%m%d")
        else:
            data[key] = value

    return data


class TestDataFileAggregationBaseMethods(TestCase):
    """
    The tests in this class test the methods in the models.FileAggregationBase
    class. This is done through the DataSubmission concrete class derived from
    the base.
    """
    def setUp(self):
        # Creates an example data submission. No files should be created on disk,
        # but the database will be altered.
        self.example_files = test_data_submission
        self.dsub = get_or_create(models.DataSubmission, status=STATUS_VALUES.ARRIVED,
            incoming_directory=test_data_submission.INCOMING_DIR,
            directory=test_data_submission.INCOMING_DIR)

        for dfile_name in self.example_files.files:
            metadata = _extract_file_metadata(os.path.join(
                test_data_submission.INCOMING_DIR, dfile_name))
            self.proj = get_or_create(models.Project, short_name="CMIP6", full_name="6th "
                "Coupled Model Intercomparison Project")
            climate_model = get_or_create(models.ClimateModel,
                short_name=metadata["climate_model"], full_name="Really good model")
            experiment = get_or_create(models.Experiment, short_name="experiment",
                full_name="Really good experiment")
            var = get_or_create(models.Variable, var_id=metadata["var_id"],
                long_name="Really good variable", units="1")

            models.DataFile.objects.create(name=dfile_name,
                incoming_directory=self.example_files.INCOMING_DIR,
                directory=self.example_files.INCOMING_DIR, size=1, project=self.proj,
                climate_model=climate_model, experiment=experiment,
                variable=var, frequency=metadata["frequency"], online=True,
                start_time=metadata["start_time"], end_time=metadata["end_time"],
                data_submission=self.dsub)

    def test_get_data_files(self):
        files = self.dsub.get_data_files()
        filenames = [df.name for df in files]

        expected = [unicode(fn) for fn in self.example_files.files]

        self.assertEqual(filenames, expected)

    def test_project(self):
        self.assertEqual(self.dsub.project(), [self.proj])

    def test_climate_model(self):
        clim_models = self.dsub.climate_model()
        model_names = [cm.short_name for cm in clim_models]
        model_names.sort()

        expected = [u'HadGEM2-ES', u'IPSL-CM5A-LR']

        self.assertEqual(model_names, expected)

    def test_frequency(self):
        frequencies = self.dsub.frequency()
        frequencies.sort()

        expected = [u'cfDay', u'day']

        self.assertEqual(frequencies, expected)

    def test_variables(self):
        variables = self.dsub.variables()
        var_names = [v.var_id for v in variables]
        var_names.sort()

        expected = ['rsds', 'tasmax', 'zos']

        self.assertEqual(var_names, expected)

    def test_start_time(self):
        start_time = self.dsub.start_time()

        expected = datetime.datetime(1859, 1, 1, 0, 0, 0, 0, pytz.utc)

        self.assertEqual(start_time, expected)

    def test_end_time(self):
        end_time = self.dsub.end_time()

        expected = datetime.datetime(1993, 12, 30, 0, 0, 0, 0, pytz.utc)

        self.assertEqual(end_time, expected)

    def test_online_status_all_online(self):
        status = self.dsub.online_status()

        self.assertEqual(status, ONLINE_STATUS.online)

    def test_online_status_some_online(self):
        datafile = self.dsub.get_data_files()[0]
        datafile.online = False
        datafile.save()

        status = self.dsub.online_status()
        self.assertEqual(status, ONLINE_STATUS.partial)

    def test_online_status_none_online(self):
        for df in self.dsub.get_data_files():
            df.online = False
            df.save()

        status = self.dsub.online_status()
        self.assertEqual(status, ONLINE_STATUS.offline)

    def test_get_data_issues(self):
        issues = self.dsub.get_data_issues()

        self.assertEqual(issues, [])

    def test_get_data_issues_with_single_issue(self):
        di = models.DataIssue(issue='unit test', reporter='bob',
            date_time=datetime.datetime(1950, 12, 13))
        di.save()

        datafile = self.dsub.get_data_files()[0]
        datafile.dataissue_set.add(di)

        issues = self.dsub.get_data_issues()

        self.assertEqual(issues, [di])

    def test_get_data_issues_with_single_issue_on_all_files(self):
        di = models.DataIssue(issue='unit test', reporter='bob',
            date_time=datetime.datetime(1950, 12, 13))
        di.save()

        for df in self.dsub.get_data_files():
            df.dataissue_set.add(di)

        issues = self.dsub.get_data_issues()

        self.assertEqual(issues, [di])

    def test_get_data_issues_with_many_issues(self):
        di1 = models.DataIssue(issue='2nd test', reporter='bill',
            date_time=datetime.datetime(1805, 7, 5))
        di1.save()
        di2 = models.DataIssue(issue='unit test', reporter='bob',
            date_time=datetime.datetime(1950, 12, 13))
        di2.save()

        datafile = self.dsub.get_data_files()[0]
        datafile.dataissue_set.add(di2)

        datafile = self.dsub.get_data_files()[1]
        datafile.dataissue_set.add(di1)

        issues = self.dsub.get_data_issues()

        self.assertEqual(issues, [di2, di1])

    def test_assign_data_issue(self):
        self.dsub.assign_data_issue('all files', 'Lewis',
            datetime.datetime(1881, 10, 11))

        for df in self.dsub.get_data_files():
            di = df.dataissue_set.filter(issue='all files')[0]
            self.assertEqual(di.reporter, 'Lewis')


class TestESGFDatasetMethods(TestCase):
    """
    Test the additional methods in the ESGFDataset class
    """
    def setUp(self):
        self.esgf_ds = get_or_create(models.ESGFDataset,
            drs_id='a.b.c.d', version='v20160720',
            directory='/some/dir')

    def test_get_full_id(self):
        full_id = self.esgf_ds.get_full_id()

        expected = 'ESGF Dataset: a.b.c.d.v20160720'

        self.assertEqual(full_id, expected)

    def test_clean_version(self):
        self.esgf_ds.version = '20160720'
        self.assertRaises(ValidationError, self.esgf_ds.clean)

    def test_clean_directory_initial_slash(self):
        self.esgf_ds.directory = '~rfitz/his_dir'
        self.assertRaises(ValidationError, self.esgf_ds.clean)

    def test_clean_directory_final_slash(self):
        self.esgf_ds.directory = '/some/dir/'
        self.esgf_ds.save()
        self.assertEqual(self.esgf_ds.directory, '/some/dir/')

        self.esgf_ds.clean()
        self.assertEqual(self.esgf_ds.directory, '/some/dir')

    def test_unicode(self):
        unicode_drs = unicode(self.esgf_ds)

        expected = 'ESGF Dataset: a.b.c.d.v20160720'

        self.assertEqual(unicode_drs, expected)
        self.assertIsInstance(unicode_drs, unicode)
