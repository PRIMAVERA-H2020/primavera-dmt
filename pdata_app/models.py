from __future__ import unicode_literals, division, absolute_import
import re

import cf_units

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from solo.models import SingletonModel
from django.db.models import PROTECT, SET_NULL, CASCADE
from django.core.exceptions import ValidationError

from pdata_app.utils.common import standardise_time_unit, safe_strftime
from vocabs import (STATUS_VALUES, FREQUENCY_VALUES, ONLINE_STATUS,
    CHECKSUM_TYPES, VARIABLE_TYPES, CALENDARS)

model_names = ['Project', 'Institute', 'ClimateModel', 'Experiment',
               'ActivityId', 'DataSubmission', 'DataFile', 'ESGFDataset',
               'CEDADataset', 'DataRequest', 'DataIssue', 'Checksum',
               'Settings', 'VariableRequest', 'RetrievalRequest', 'EmailQueue',
               'ReplacedFile', 'ObservationDataset', 'ObservationFile']
__all__ = model_names


class Settings(SingletonModel):
    """
    Global settings for the app (that can be changed within the app
    """
    is_paused = models.BooleanField(default=False, null=False)
    standard_time_units = models.CharField(max_length=50,
        verbose_name='Standard Time Units', default='days since 1950-01-01')
    contact_user_id = models.CharField(max_length=20,
                                       verbose_name='Contact User ID',
                                       default='jseddon')
    base_output_dir = models.CharField(max_length=300,
                                       verbose_name='Base directory for '
                                                    'retrieved files',
                                       default='/group_workspaces/jasmin2/'
                                               'primavera5/stream1')
    current_stream1_dir = models.CharField(
        max_length=300,
        verbose_name='The directory that retrievals are currently being '
                     'retrieved to.',
        default='/group_workspaces/jasmin2/primavera4/stream1'
    )

    class Meta:
        verbose_name = "Settings"

    def __str__(self):
        return "App Settings"


class Project(models.Model):
    """
    A project
    """
    # RFK Relationships
    # DataFile

    short_name = models.CharField(max_length=100, null=False,
        blank=False, unique=True)
    full_name = models.CharField(max_length=300, null=False, blank=False)

    def __str__(self):
        return self.short_name


class Institute(models.Model):
    """
    An institute
    """
    # RFK Relationships
    # DataRequest

    short_name = models.CharField(max_length=100, null=False,
        blank=False, unique=True)
    full_name = models.CharField(max_length=1000, null=False, blank=False)

    def __str__(self):
        return self.short_name


class ClimateModel(models.Model):
    """
    A climate model
    """
    # RFK Relationships
    # DataFile
    # DataRequest

    short_name = models.CharField(max_length=100, null=False,
                                  blank=False, unique=True)
    full_name = models.CharField(max_length=300, null=False, blank=False)

    def __str__(self):
        return self.short_name

    class Meta:
        verbose_name = "Climate Model"


class Experiment(models.Model):
    """
    An experiment
    """
    # RFK Relationships
    # DataFile
    # DataRequest

    short_name = models.CharField(max_length=100, null=False,
                                  blank=False, unique=True)
    full_name = models.CharField(max_length=300, null=False, blank=False)

    def __str__(self):
        return self.short_name


class ActivityId(models.Model):
    """
    An activity id
    """
    # RFK Relationships
    # DataFile

    short_name = models.CharField(max_length=100, null=False,
        blank=False, unique=True)
    full_name = models.CharField(max_length=300, null=False, blank=False)

    def __str__(self):
        return self.short_name

    class Meta:
        verbose_name = 'Activity ID'


class VariableRequest(models.Model):
    """
    A variable requested in the CMIP6 data request
    """
    table_name = models.CharField(max_length=30, null=False, blank=False,
                                  verbose_name='Table Name')
    long_name = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Long Name')
    units = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Units')
    var_name = models.CharField(max_length=30, null=False, blank=False,
                                  verbose_name='Var Name')
    standard_name = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Standard Name')
    cell_methods = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Cell Methods')
    positive = models.CharField(max_length=20, null=True, blank=True,
                                  verbose_name='Positive')
    variable_type = models.CharField(max_length=20,
                                     choices=list(VARIABLE_TYPES.items()),
                                     null=False, blank=False,
                                  verbose_name='Variable Type')
    dimensions = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Dimensions')
    cmor_name = models.CharField(max_length=20, null=False, blank=False,
                                  verbose_name='CMOR Name')
    modeling_realm = models.CharField(max_length=20, null=False, blank=False,
                                  verbose_name='Modeling Realm')
    frequency = models.CharField(max_length=200,
                                 choices=list(FREQUENCY_VALUES.items()),
                                 null=False, blank=False,
                                  verbose_name='Frequency')
    cell_measures = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='Cell Measures')
    uid = models.CharField(max_length=200, null=False, blank=False,
                                  verbose_name='UID')

    def __str__(self):
        return 'VariableRequest: {} ({})'.format(self.cmor_name, self.table_name)

    class Meta:
        verbose_name = "Variable Request"


class DataFileAggregationBase(models.Model):
    """
    An abstract base class for datasets containing many files.

    Includes a number of convenience methods to calculate
    aggregations of properties.
    """
    class Meta:
        abstract = True

    def _file_aggregation(self, field_name):
        records = [getattr(datafile, field_name) for datafile in self.get_data_files()]
        # Return unique sorted set of records
        unique_records = sorted(set(records))
        if unique_records == [None]:
            return None
        else:
            return unique_records

    def get_data_files(self):
        return self.datafile_set.all()

    def project(self):
        return self._file_aggregation("project")

    def climate_model(self):
        return self._file_aggregation("climate_model")

    def frequency(self):
        return self._file_aggregation("frequency")

    def variables(self):
        return self._file_aggregation("variable_request")

    def get_tape_urls(self):
        return self._file_aggregation("tape_url")

    def get_file_versions(self):
        return self._file_aggregation("version")

    def get_data_issues(self):
        records = []
        for datafile in self.get_data_files():
            records.extend(datafile.dataissue_set.all())

        records = list(set(records))
        records.sort(key=lambda di: di.date_time, reverse=True)
        return records

    def assign_data_issue(self, issue_text, reporter, date_time=None):
        """
        Creates a DataIssue and attaches it to all related DataFile records.
        """
        date_time = date_time or timezone.now()
        data_issue, _tf = DataIssue.objects.get_or_create(issue=issue_text,
            reporter=reporter, date_time=date_time)
        data_issue.save()

        data_files = self.get_data_files()
        data_issue.data_file.add(*data_files)

    def start_time(self):
        std_units = Settings.get_solo().standard_time_units

        start_times = self.datafile_set.values_list('start_time', 'time_units',
            'calendar')

        if not start_times:
            return None

        std_times = [
            (standardise_time_unit(time, unit, std_units, cal), cal)
            for time, unit, cal in start_times
        ]

        none_values_removed = [(std_time, cal)
                               for std_time, cal in std_times
                               if std_time is not None]

        if not none_values_removed:
            return None

        earliest_time, calendar = min(none_values_removed, key=lambda x: x[0])

        earliest_obj = cf_units.num2date(earliest_time, std_units, calendar)

        return earliest_obj.strftime('%Y-%m-%d')

    def end_time(self):
        std_units = Settings.get_solo().standard_time_units

        end_times = self.datafile_set.values_list('end_time', 'time_units',
            'calendar')

        if not end_times:
            return None

        std_times = [
            (standardise_time_unit(time, unit, std_units, cal), cal)
            for time, unit, cal in end_times
        ]

        none_values_removed = [(std_time, cal)
                               for std_time, cal in std_times
                               if std_time is not None]

        if not none_values_removed:
            return None

        latest_time, calendar = max(none_values_removed, key=lambda x: x[0])

        latest_obj = cf_units.num2date(latest_time, std_units, calendar)

        return latest_obj.strftime('%Y-%m-%d')

    def online_status(self):
        """
        Checks aggregation of online status of all DataFiles.
        Returns one of:
            ONLINE_STATUS.online
            ONLINE_STATUS.offline
            ONLINE_STATUS.partial
        """
        files_online = self.datafile_set.filter(online=True).count()
        files_offline = self.datafile_set.filter(online=False).count()

        if files_offline:
            if files_online:
                return ONLINE_STATUS.partial
            else:
                return ONLINE_STATUS.offline
        else:
            return ONLINE_STATUS.online


class DataSubmission(DataFileAggregationBase):
    """
    A directory containing a directory tree of data files copied to the
    platform.
    """

    # RFK relationships:
    # ESGFDatasets: ESGFDataset
    # DataFiles:        DataFile

    # Dynamically aggregated from DataFile information:
    # project
    # climate_model
    # frequency
    # variables
    # data_issues
    # start_time
    # end_time

    status = models.CharField(max_length=20, choices=list(STATUS_VALUES.items()),
                              verbose_name='Status',
                              default=STATUS_VALUES.EXPECTED,
                              blank=False, null=False)
    incoming_directory = models.CharField(max_length=500,
                                          verbose_name='Incoming Directory',
                                          blank=False, null=False)
    # Current directory
    directory = models.CharField(max_length=500,
                                 verbose_name='Current Directory',
                                 blank=True, null=True)
    user = models.ForeignKey(User, blank=False, null=False,
                             verbose_name='User', on_delete=models.CASCADE)
    date_submitted = models.DateTimeField(auto_now_add=True,
                                          verbose_name='Date Submitted',
                                          null=False, blank=False)

    def __str__(self):
        return "Data Submission: %s" % self.incoming_directory

    class Meta:
        unique_together = ('incoming_directory',)
        verbose_name = "Data Submission"


class CEDADataset(DataFileAggregationBase):
    """
    A CEDA Dataset - a collection of ESGF Datasets that are held in the
    CEDA Data catalogue (http://catalogue.ceda.ac.uk) with their own metadata
    records.
    """
    # RFK relationships:
    # ESGFDataset

    # Dynamically aggregated from DataFile information:
    # project
    # climate_model
    # frequency
    # variables
    # data_issues
    # start_time
    # end_time

    catalogue_url = models.URLField(verbose_name="CEDA Catalogue URL", blank=False, null=False)
    directory = models.CharField(max_length=500, verbose_name="Directory", blank=False, null=False)

    # The CEDA Dataset might have a DOI
    doi = models.CharField(verbose_name="DOI", blank=True, null=True,
                           max_length=500)

    def __str__(self):
        return "CEDA Dataset: %s" % self.catalogue_url

    class Meta:
        verbose_name = "CEDA Dataset"


class ESGFDataset(DataFileAggregationBase):
    """
    An ESGF Dataset - a collection of files with an identifier.

    This model uses the Directory Reference Syntax (DRS) dataset which consists of:
        * drs_id - string representing facets of the DRS, e.g. "a.b.c.d"
        * version - string representing the version, e.g. "v20160312"
        * directory - string representing the directory containing the actual data files.
    And a method:
        * get_full_id: Returns full DRS Id made up of drsId version as: `self.drs_id`.`self.version`.
    """
    class Meta:
        unique_together = ('drs_id', 'version')
        verbose_name = "ESGF Dataset"

    # RFK relationships:
    # files: DataFile

    # Dynamically aggregated from DataFile information:
    # project
    # climate_model
    # frequency
    # variables
    # data_issues
    # start_time
    # end_time

    drs_id = models.CharField(max_length=500, verbose_name='DRS Dataset Identifier', blank=False, null=False)
    version = models.CharField(max_length=20, verbose_name='Version', blank=False, null=False)
    directory = models.CharField(max_length=500, verbose_name='Directory', blank=False, null=False)

    thredds_url = models.URLField(verbose_name="THREDDS Download URL", blank=True, null=True)

    # Each ESGF Dataset will be part of one CEDADataset
    ceda_dataset = models.ForeignKey(CEDADataset, blank=True, null=True,
        on_delete=SET_NULL, verbose_name='CEDA Dataset')

    # Each ESGF Dataset will be part of one submission
    data_submission = models.ForeignKey(DataSubmission, blank=True, null=True,
        on_delete=SET_NULL, verbose_name='Data Submission')

    def get_full_id(self):
        """
        Return full DRS Id made up of drsId version as: drs_id.version
        """
        return "%s.%s" % (self.drs_id, self.version)

    def clean(self, *args, **kwargs):
        if not re.match(r"^v\d+$", self.version):
            raise ValidationError('Version must begin with letter "v" followed '
                                  'by a number (date).')

        if not self.directory.startswith("/"):
            raise ValidationError('Directory must begin with "/" because it is '
                                  'a full directory path.')

        if self.directory.endswith("/"):
            self.directory = self.directory.rstrip("/")

        super(ESGFDataset, self).save(*args, **kwargs)

    def __str__(self):
        """
        Returns full DRS Id.
        """
        return self.get_full_id()


class DataRequest(DataFileAggregationBase):
    """
    A Data Request for a given set of inputs
    """
    class Meta:
        verbose_name = 'Data Request'

    project = models.ForeignKey(Project, null=False, on_delete=PROTECT,
                                verbose_name='Project')
    institute = models.ForeignKey(Institute, null=False, on_delete=PROTECT,
                                  verbose_name='Institute')
    climate_model = models.ForeignKey(ClimateModel, null=False,
                                      on_delete=PROTECT,
                                      verbose_name='Climate Model')
    experiment = models.ForeignKey(Experiment, null=False, on_delete=PROTECT,
                                   verbose_name='Experiment')
    variable_request = models.ForeignKey(VariableRequest, null=False,
                                         on_delete=PROTECT,
                                         verbose_name='Variable')
    rip_code = models.CharField(max_length=20, verbose_name="Variant Label",
                                null=True, blank=True)
    request_start_time = models.FloatField(verbose_name="Start time",
                                           null=False, blank=False)
    request_end_time = models.FloatField(verbose_name="End time", null=False,
                                         blank=False)
    time_units = models.CharField(verbose_name='Time units', max_length=50,
                                  null=False, blank=False)
    calendar = models.CharField(verbose_name='Calendar', max_length=20,
                                null=False, blank=False,
                                choices=list(CALENDARS.items()))

    def start_date_string(self):
        """Return a string containing the start date"""
        dto = cf_units.num2date(self.request_start_time, self.time_units,
                                self.calendar)
        return dto.strftime('%Y-%m-%d')

    def end_date_string(self):
        """Return a string containing the end date"""
        dto = cf_units.num2date(self.request_end_time, self.time_units,
                                self.calendar)
        return dto.strftime('%Y-%m-%d')

    def __str__(self):
        return '{}/{} {}/{}/{}'.format(self.institute, self.climate_model,
                                       self.experiment,
                                       self.variable_request.table_name,
                                       self.variable_request.cmor_name)


class DataFile(models.Model):
    """
    A data file
    """

    # RFK relationships:
    # checksums: Checksum - multiple is OK

    # ManyToMany relationships:
    # DataIssues: DataIssue - multiple is OK

    name = models.CharField(max_length=200, verbose_name="File name", null=False, blank=False)
    incoming_directory = models.CharField(max_length=500, verbose_name="Incoming directory", null=False, blank=False)

    # This is where the datafile is now
    directory = models.CharField(max_length=500,
                                 verbose_name="Current directory",
                                 null=True, blank=True)
    size = models.BigIntegerField(null=False, verbose_name="File size")

    # This is the file's version
    version = models.CharField(max_length=10, verbose_name='File Version',
                               null=True, blank=True)

    # Scientific metadata
    project = models.ForeignKey(Project, null=False, on_delete=PROTECT)
    institute = models.ForeignKey(Institute, null=False, on_delete=PROTECT,
                                  verbose_name='Institute')
    climate_model = models.ForeignKey(ClimateModel, null=False,
                                      on_delete=PROTECT,
                                      verbose_name='Climate Model')
    activity_id = models.ForeignKey(ActivityId, null=False,
                                      on_delete=PROTECT,
                                      verbose_name='Activity ID')
    experiment = models.ForeignKey(Experiment, null=False, on_delete=PROTECT,
                                   verbose_name='Experiment')
    variable_request = models.ForeignKey(VariableRequest, null=False, on_delete=PROTECT)
    data_request = models.ForeignKey(DataRequest, null=False, on_delete=PROTECT)
    frequency = models.CharField(max_length=20, choices=list(FREQUENCY_VALUES.items()),
        verbose_name="Time frequency", null=False, blank=False)
    rip_code = models.CharField(max_length=20, verbose_name="Variant Label",
                                null=False, blank=False)
    grid = models.CharField(max_length=20, verbose_name='Grid Label',
                            null=True, blank=True)

    # DateTimes are allowed to be null/blank because some fields (such as orography)
    # are time-independent
    start_time = models.FloatField(verbose_name="Start time", null=True, blank=True)
    end_time = models.FloatField(verbose_name="End time", null=True, blank=True)
    time_units = models.CharField(verbose_name='Time units', max_length=50, null=True, blank=True)
    calendar = models.CharField(verbose_name='Calendar', max_length=20,
        null=True, blank=True, choices=list(CALENDARS.items()))

    data_submission = models.ForeignKey(DataSubmission, null=False, blank=False,
        on_delete=CASCADE)

    # These Dataset fields might only be known after processing so they can be null/blank
    esgf_dataset = models.ForeignKey(ESGFDataset, null=True, blank=True,
        on_delete=SET_NULL)
    ceda_dataset = models.ForeignKey(CEDADataset, null=True, blank=True,
        on_delete=SET_NULL)

    # URLs will not be known at start so can be blank
    ceda_download_url = models.URLField(verbose_name="CEDA Download URL", null=True, blank=True)
    ceda_opendap_url = models.URLField(verbose_name="CEDA OpenDAP URL", null=True, blank=True)

    esgf_download_url = models.URLField(verbose_name="ESGF Download URL", null=True, blank=True)
    esgf_opendap_url = models.URLField(verbose_name="ESGF OpenDAP URL", null=True, blank=True)

    # Tape status
    online = models.BooleanField(default=True, verbose_name="Is the file online?", null=False, blank=False)
    tape_url = models.CharField(verbose_name="Tape URL", max_length=200, null=True, blank=True)

    def start_date_string(self):
        """Return a string containing the start date"""
        dto = cf_units.num2date(self.start_time, self.time_units, self.calendar)
        return dto.strftime('%Y-%m-%d')

    def end_date_string(self):
        """Return a string containing the end date"""
        dto = cf_units.num2date(self.end_time, self.time_units, self.calendar)
        return dto.strftime('%Y-%m-%d')

    def __str__(self):
        return "%s (Directory: %s)" % (self.name, self.directory)

    class Meta:
        unique_together = ('name', 'directory')
        verbose_name = "Data File"


class ReplacedFile(models.Model):
    """
    An old DataFile that has been replaced by another DataFile
    """
    name = models.CharField(max_length=200, verbose_name="File name",
                            null=False, blank=False)
    incoming_directory = models.CharField(max_length=500,
                                          verbose_name="Incoming directory",
                                          null=False, blank=False)

    size = models.BigIntegerField(null=False, verbose_name="File size")

    # This is the file's version
    version = models.CharField(max_length=10, verbose_name='File Version',
                               null=True, blank=True)

    # Scientific metadata
    project = models.ForeignKey(Project, null=False, on_delete=PROTECT)
    institute = models.ForeignKey(Institute, null=False, on_delete=PROTECT,
                                  verbose_name='Institute')
    climate_model = models.ForeignKey(ClimateModel, null=False,
                                      on_delete=PROTECT,
                                      verbose_name='Climate Model')
    activity_id = models.ForeignKey(ActivityId, null=False,
                                    on_delete=PROTECT,
                                    verbose_name='Activity ID')
    experiment = models.ForeignKey(Experiment, null=False, on_delete=PROTECT,
                                   verbose_name='Experiment')
    variable_request = models.ForeignKey(VariableRequest, null=False,
                                         on_delete=PROTECT)
    data_request = models.ForeignKey(DataRequest, null=False,
                                     on_delete=PROTECT)
    frequency = models.CharField(max_length=20,
                                 choices=list(FREQUENCY_VALUES.items()),
                                 verbose_name="Time frequency",
                                 null=False, blank=False)
    rip_code = models.CharField(max_length=20, verbose_name="Variant Label",
                                null=False, blank=False)
    grid = models.CharField(max_length=20, verbose_name='Grid Label',
                            null=True, blank=True)

    # DateTimes are allowed to be null/blank because some fields (such as
    # orography) are time-independent
    start_time = models.FloatField(verbose_name="Start time",
                                   null=True, blank=True)
    end_time = models.FloatField(verbose_name="End time",
                                 null=True, blank=True)
    time_units = models.CharField(verbose_name='Time units', max_length=50,
                                  null=True, blank=True)
    calendar = models.CharField(verbose_name='Calendar', max_length=20,
                                null=True, blank=True,
                                choices=list(CALENDARS.items()))

    data_submission = models.ForeignKey(DataSubmission,
                                        null=False, blank=False,
                                        on_delete=CASCADE)

    # Tape status
    tape_url = models.CharField(verbose_name="Tape URL", max_length=200,
                                null=True, blank=True)

    # Checksum
    checksum_value = models.CharField(max_length=200, null=True, blank=True)
    checksum_type = models.CharField(max_length=20,
                                     choices=list(CHECKSUM_TYPES.items()),
                                     null=True, blank=True)

    def start_date_string(self):
        """Return a string containing the start date"""
        dto = cf_units.num2date(self.start_time, self.time_units,
                                self.calendar)
        return dto.strftime('%Y-%m-%d')

    def end_date_string(self):
        """Return a string containing the end date"""
        dto = cf_units.num2date(self.end_time, self.time_units, self.calendar)
        return dto.strftime('%Y-%m-%d')

    def __str__(self):
        return "%s (Directory: %s)" % (self.name, self.directory)

    class Meta:
        unique_together = ('name', 'incoming_directory')
        verbose_name = "Replaced File"


class DataIssue(models.Model):
    """
    A recorded issue with a DataFile

    NOTE: You can have multiple data issues related to a single DataFile
    NOTE: Aggregation is used to associate a DataIssue with an ESGFDataset,
    CEDADataset or DataSubmission
    """
    issue = models.CharField(max_length=4000, verbose_name="Issue Reported",
                             null=False, blank=False)
    reporter = models.ForeignKey(User, verbose_name="Reporter",
                                 null=False, blank=False,
                                 on_delete=models.CASCADE)
    date_time = models.DateTimeField(auto_now_add=True,
                                     verbose_name="Date and Time of Report",
                                     null=False, blank=False)

    # DataFile that the Data Issue corresponds to
    data_file = models.ManyToManyField(DataFile)

    def __str__(self):
        return "Data Issue (%s): %s (%s)" % (
            self.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            self.issue, self.reporter.username
        )

    class Meta:
        verbose_name = "Data Issue"


class Checksum(models.Model):
    """
    A checksum
    """
    data_file = models.ForeignKey(DataFile, null=False, blank=False,
        on_delete=CASCADE)
    checksum_value = models.CharField(max_length=200, null=False, blank=False)
    checksum_type = models.CharField(max_length=20, choices=list(CHECKSUM_TYPES.items()), null=False,
                                     blank=False)

    def __str__(self):
        return "%s: %s (%s)" % (self.checksum_type, self.checksum_value,
                                self.data_file.name)


class RetrievalRequest(models.Model):
    """
    A collection of DataRequests to retrieve from Elastic Tape or MASS
    """
    class Meta:
        verbose_name = "Retrieval Request"

    data_request = models.ManyToManyField(DataRequest)

    date_created = models.DateTimeField(auto_now_add=True,
                                        verbose_name='Request Created At',
                                        null=False, blank=False)
    date_complete = models.DateTimeField(verbose_name='Data Restored At',
                                         null=True, blank=True)
    date_deleted = models.DateTimeField(verbose_name='Data Deleted At',
                                         null=True, blank=True)

    requester = models.ForeignKey(User, verbose_name='Request Creator',
                                  null=False, blank=False,
                                  on_delete=models.CASCADE)

    data_finished = models.BooleanField(default=False,
                                        verbose_name="Data Finished?",
                                        null=False, blank=False)

    start_year = models.IntegerField(verbose_name="Start Year", null=True, blank=False)
    end_year = models.IntegerField(verbose_name="End Year", null=True, blank=False)

    def __str__(self):
        return '{}'.format(self.id)


class EmailQueue(models.Model):
    """
    A collection of emails that have been queued to send
    """
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)

    subject = models.CharField(max_length=400, blank=False)

    message = models.TextField(blank=False)

    sent = models.BooleanField(default=False, null=False)

    def __str__(self):
        return '{} {}'.format(self.recipient.email, self.subject)


class ObservationDataset(models.Model):
    """
    A collection of observation files.
    """
    class Meta:
        unique_together = ('name', 'version')
        verbose_name = 'Observations Dataset'

    name = models.CharField(max_length=200,
                            verbose_name='Name',
                            null=True, blank=True)
    version = models.CharField(max_length=200, verbose_name='Version',
                               null=True, blank=True)

    url = models.URLField(verbose_name='URL', null=True, blank=True)
    summary = models.CharField(max_length=4000, verbose_name='Summary',
                               null=True, blank=True)
    date_downloaded = models.DateTimeField(verbose_name='Date downloaded',
                                           null=True, blank=True)

    doi = models.CharField(max_length=200, verbose_name='DOI',
                           null=True, blank=True)

    reference = models.CharField(max_length=4000, verbose_name='Reference',
                                 null=True, blank=True)

    license = models.URLField(verbose_name='License', null=True, blank=True)

    # The following cached fields can be calculated from the foreign key
    # relationships. Howevere due to the number of observation files this
    # can be slow. Instead a script is run by a cron job to periodically
    # save the information here to speed page load.
    cached_variables = models.CharField(max_length=1000,
                                        verbose_name='Variables',
                                        null=True, blank=True)
    cached_start_time = models.DateTimeField(verbose_name='Start Time',
                                             null=True, blank=True)
    cached_end_time = models.DateTimeField(verbose_name='End Time',
                                           null=True, blank=True)
    cached_num_files = models.IntegerField(verbose_name='# Data Files',
                                           null=True, blank=True)
    cached_directories = models.CharField(max_length=200,
                                          verbose_name='Directory',
                                          null=True, blank=True)

    def _file_aggregation(self, field_name):
        records = [getattr(obs_file, field_name)
                   for obs_file in self.obs_files]
        # Return unique sorted set of records
        unique_records = sorted(set(records))
        if None in unique_records:
            unique_records.remove(None)
        if unique_records == []:
            return None
        else:
            return unique_records

    @property
    def obs_files(self):
        return self.observationfile_set.all()

    @property
    def variables(self):
        var_strings = self._file_aggregation('variable')

        if var_strings:
            all_vars = [indi_var.strip() for var_string in var_strings
                        for indi_var in var_string.split(',')]
            return sorted(list(set(all_vars)))
        else:
            return None

    @property
    def incoming_directories(self):
        return self._file_aggregation('incoming_directory')

    @property
    def directories(self):
        return self._file_aggregation('directory')

    @property
    def tape_urls(self):
        return self._file_aggregation('tape_url')

    @property
    def frequencies(self):
        return self._file_aggregation('frequency')

    @property
    def units(self):
        return self._file_aggregation('units')

    @property
    def start_time(self):
        std_units = Settings.get_solo().standard_time_units

        start_times = self.obs_files.values_list('start_time', 'time_units',
                                                 'calendar')

        if not start_times:
            return None

        std_times = [
            (standardise_time_unit(time, unit, std_units, cal), cal)
            for time, unit, cal in start_times
        ]

        none_values_removed = [(std_time, cal)
                               for std_time, cal in std_times
                               if std_time is not None]

        if not none_values_removed:
            return None

        earliest_time, calendar = min(none_values_removed, key=lambda x: x[0])

        earliest_obj = cf_units.num2date(earliest_time, std_units, calendar)

        return earliest_obj

    @property
    def end_time(self):
        std_units = Settings.get_solo().standard_time_units

        end_times = self.obs_files.values_list('end_time', 'time_units',
                                               'calendar')

        if not end_times:
            return None

        std_times = [
            (standardise_time_unit(time, unit, std_units, cal), cal)
            for time, unit, cal in end_times
        ]

        none_values_removed = [(std_time, cal)
                               for std_time, cal in std_times
                               if std_time is not None]

        if not none_values_removed:
            return None

        latest_time, calendar = max(none_values_removed, key=lambda x: x[0])

        latest_obj = cf_units.num2date(latest_time, std_units, calendar)

        return latest_obj

    @property
    def online_status(self):
        """
        Checks aggregation of online status of all DataFiles.
        Returns one of:
            ONLINE_STATUS.online
            ONLINE_STATUS.offline
            ONLINE_STATUS.partial
        """
        files_online = self.obs_files.filter(online=True).count()
        files_offline = self.obs_files.filter(online=False).count()

        if files_offline:
            if files_online:
                return ONLINE_STATUS.partial
            else:
                return ONLINE_STATUS.offline
        else:
            return ONLINE_STATUS.online

    def __str__(self):
        if self.version:
            return '{} ver {}'.format(self.name, self.version)
        else:
            return '{}'.format(self.name)


class ObservationFile(models.Model):
    """
    A single file containing observations or a reanalysis.
    """
    class Meta:
        unique_together = ('name', 'incoming_directory')
        verbose_name = 'Observations File'

    name = models.CharField(max_length=200, verbose_name='File name',
                            null=False, blank=False)

    incoming_directory = models.CharField(max_length=500,
                                          verbose_name='Incoming directory',
                                          null=False, blank=False)
    directory = models.CharField(max_length=200, verbose_name='Directory',
                                 null=True, blank=True)
    tape_url = models.CharField(verbose_name="Tape URL", max_length=200,
                                null=True, blank=True)
    online = models.BooleanField(default=True, null=False, blank=False,
                                 verbose_name='Is the file online?')
    size = models.BigIntegerField(null=False, verbose_name='File size')

    checksum_value = models.CharField(max_length=200, null=True, blank=True)
    checksum_type = models.CharField(max_length=20,
                                     choices=list(CHECKSUM_TYPES.items()),
                                     null=True, blank=True)

    # DateTimes are allowed to be null/blank because some fields (such as
    # orography) are time-independent
    start_time = models.FloatField(verbose_name="Start time",
                                   null=True, blank=True)
    end_time = models.FloatField(verbose_name="End time",
                                 null=True, blank=True)
    time_units = models.CharField(verbose_name='Time units', max_length=50,
                                  null=True, blank=True)
    calendar = models.CharField(verbose_name='Calendar', max_length=20,
                                null=True, blank=True,
                                choices=list(CALENDARS.items()))
    frequency = models.CharField(max_length=200, null=True, blank=True,
                                 verbose_name='Frequency')

    # Details of the variables in the file
    standard_name = models.CharField(max_length=500, null=True, blank=True,
                                     verbose_name='Standard name')
    long_name = models.CharField(max_length=500, null=True, blank=True,
                                 verbose_name='Long name')
    var_name = models.CharField(max_length=200, null=True, blank=True,
                                verbose_name='Var name')
    units = models.CharField(max_length=200, null=True, blank=True,
                             verbose_name='Units')

    @property
    def variable(self):
        if self.standard_name:
            return self.standard_name
        elif self.long_name:
            return self.long_name
        elif self.var_name:
            return self.var_name
        else:
            return None

    @property
    def start_string(self):
        if self.start_time is not None and self.time_units and self.calendar:
            return safe_strftime(
                cf_units.num2date(self.start_time, self.time_units,
                                     self.calendar), '%Y-%m-%d')
        else:
            return None

    @property
    def end_string(self):
        if self.end_time is not None and self.time_units and self.calendar:
            return safe_strftime(
                cf_units.num2date(self.end_time, self.time_units,
                                     self.calendar), '%Y-%m-%d')
        else:
            return None

    # Foreign Key Relationships
    obs_set = models.ForeignKey(ObservationDataset, null=False, blank=False,
                                on_delete=CASCADE, verbose_name='Obs Set')

    def __str__(self):
        return '{} (Directory: {})'.format(self.name, self.incoming_directory)
