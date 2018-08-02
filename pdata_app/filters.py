from __future__ import unicode_literals, division, absolute_import
from django.db.models import Q
import django_filters
from .models import (DataRequest, DataSubmission, DataFile, ESGFDataset,
                     CEDADataset, DataIssue, VariableRequest, RetrievalRequest,
                     ReplacedFile, ObservationDataset, ObservationFile)


def patched_label():
    """
    This is a monkey patch that is applied to
    django_filters.filters.Filter.label that checks for the existence of
    `model`.
    """
    def fget(self):
        if self._label is None and hasattr(self, 'parent'):
            model = self.parent._meta.model
            if model:
                self._label = label_for_filter(
                    model, self.field_name, self.lookup_expr, self.exclude
                )
        return self._label

    def fset(self, value):
        self._label = value

    return locals()


# Monkey patch the failing function for broken version
if django_filters.__version__ == '1.1.0':
    django_filters.filters.Filter.label = patched_label


class DataRequestFilter(django_filters.FilterSet):
    class Meta:
        model = DataRequest
        fields = ['project', 'institute', 'climate_model', 'experiment',
                  'variable_request', 'rip_code']

    project = django_filters.CharFilter(field_name='project__short_name',
                                        lookup_expr='icontains')

    institute = django_filters.CharFilter(field_name='institute__short_name',
                                          lookup_expr='icontains')

    climate_model = django_filters.CharFilter(
        field_name='climate_model__short_name',
        lookup_expr='icontains'
    )

    experiment = django_filters.CharFilter(field_name='experiment__short_name',
                                           lookup_expr='icontains')

    cmor_name = django_filters.CharFilter(
        field_name='variable_request__cmor_name',
        lookup_expr='iexact'
    )

    var_name = django_filters.CharFilter(
        field_name='variable_request__var_name',
        lookup_expr='iexact'
    )

    mip_table = django_filters.CharFilter(
        field_name='variable_request__table_name',
        lookup_expr='iexact'
    )

    rip_code = django_filters.CharFilter(field_name='rip_code',
                                         lookup_expr='icontains')


class DataFileFilter(django_filters.FilterSet):
    class Meta:
        model = DataFile
        fields = ['name', 'directory', 'version', 'tape_url',
                  'data_submission', 'data_issue', 'data_request', 'grid',
                  'variable_request', 'institute', 'climate_model',
                  'experiment', 'rip_code']

    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='icontains')

    directory = django_filters.CharFilter(field_name='directory',
                                          lookup_expr='icontains')

    version = django_filters.CharFilter(field_name='version',
                                        lookup_expr='icontains')

    tape_url = django_filters.CharFilter(field_name='tape_url',
                                         lookup_expr='icontains')

    data_submission = django_filters.NumberFilter(
        field_name='data_submission__id'
    )

    data_issue = django_filters.NumberFilter(field_name='dataissue__id')

    data_request = django_filters.NumberFilter(field_name='data_request__id')

    grid = django_filters.CharFilter(field_name='grid',
                                     lookup_expr='icontains')

    cmor_name = django_filters.CharFilter(
        field_name='variable_request__cmor_name',
        lookup_expr='iexact'
    )

    mip_table = django_filters.CharFilter(
        field_name='variable_request__table_name',
        lookup_expr='iexact'
    )

    institute = django_filters.CharFilter(field_name='institute__short_name',
                                          lookup_expr='icontains')

    climate_model = django_filters.CharFilter(
        field_name='climate_model__short_name',
        lookup_expr='icontains')

    experiment = django_filters.CharFilter(
        field_name='experiment__short_name',
        lookup_expr='icontains'
    )

    rip_code = django_filters.CharFilter(field_name='rip_code',
                                         lookup_expr='icontains')


class DataSubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = DataSubmission
        fields = ('status', 'directory', 'user')

    status = django_filters.CharFilter(field_name='status',
                                       lookup_expr='icontains')

    directory = django_filters.CharFilter(field_name='directory',
                                          lookup_expr='icontains')

    version = django_filters.CharFilter(field_name='datafile__version',
                                        lookup_expr='icontains')

    tape_url = django_filters.CharFilter(field_name='datafile__tape_url',
                                         lookup_expr='icontains')

    user = django_filters.CharFilter(field_name='user__username',
                                     lookup_expr='icontains')


class ESGFDatasetFilter(django_filters.FilterSet):
    class Meta:
        models = ESGFDataset
        fields = ('drs_id', 'version', 'directory', 'thredds_urls',
                  'ceda_dataset', 'data_submission')

    drs_id = django_filters.CharFilter(field_name='drs_id',
                                       lookup_expr='icontains')

    version = django_filters.CharFilter(field_name='version',
                                        lookup_expr='icontains')

    directory = django_filters.CharFilter(field_name='directory',
                                          lookup_expr='icontains')

    thredds_url = django_filters.CharFilter(field_name='thredds_url',
                                            lookup_expr='icontains')

    ceda_dataset = django_filters.CharFilter(
        field_name='ceda_dataset__directory',
        lookup_expr='icontains'
    )

    data_submission = django_filters.CharFilter(
        field_name='data_submission__directory',
        lookup_expr='icontains'
    )


class CEDADatasetFilter(django_filters.FilterSet):
    class Meta:
        models = CEDADataset
        fields = ('catalogue_url', 'directory', 'doi')

    catalogue_url = django_filters.CharFilter(field_name='catalogue_url',
                                              lookup_expr='icontains')

    directory = django_filters.CharFilter(field_name='directory',
                                          lookup_expr='icontains')

    doi = django_filters.CharFilter(field_name='doi', lookup_expr='icontains')


class DataIssueFilter(django_filters.FilterSet):
    class Meta:
        models = DataIssue
        fields = ('issue', 'reporter', 'date_time', 'id', 'data_file')

    id = django_filters.NumberFilter(field_name='id')

    issue = django_filters.CharFilter(field_name='issue',
                                      lookup_expr='icontains')

    reporter = django_filters.CharFilter(field_name='reporter__username',
                                         lookup_expr='icontains')

    date_time = django_filters.DateFromToRangeFilter(field_name='date_time')

    data_file = django_filters.NumberFilter(field_name='data_file__id')

    data_submission = django_filters.NumberFilter(
        field_name='data_file__data_submission__id')

    data_request = django_filters.NumberFilter(
        field_name='data_file__data_request__id')


class VariableRequestQueryFilter(django_filters.FilterSet):
    class Meta:
        models = VariableRequest
        fields = ('table_name', 'long_name', 'units', 'var_name',
                  'standard_name', 'cell_methods', 'positive', 'variable_type',
                  'dimensions', 'cmor_name', 'modeling_realm', 'frequency',
                  'cell_measures', 'uid')

    table_name = django_filters.CharFilter(field_name='table_name',
                                           lookup_expr='icontains')

    long_name = django_filters.CharFilter(field_name='long_name',
                                          lookup_expr='icontains')

    units = django_filters.CharFilter(field_name='units',
                                      lookup_expr='icontains')

    var_name = django_filters.CharFilter(field_name='var_name',
                                         lookup_expr='icontains')

    standard_name = django_filters.CharFilter(field_name='standard_name',
                                              lookup_expr='icontains')

    cell_methods = django_filters.CharFilter(field_name='cell_methods',
                                             lookup_expr='icontains')

    positive = django_filters.CharFilter(field_name='positive',
                                         lookup_expr='icontains')

    variable_type = django_filters.CharFilter(field_name='variable_type',
                                              lookup_expr='icontains')

    dimensions = django_filters.CharFilter(field_name='dimensions',
                                           lookup_expr='icontains')

    cmor_name = django_filters.CharFilter(field_name='cmor_name',
                                          lookup_expr='iexact')

    modeling_realm = django_filters.CharFilter(field_name='modeling_realm',
                                               lookup_expr='icontains')

    frequency = django_filters.CharFilter(field_name='frequency',
                                          lookup_expr='icontains')

    cell_measures = django_filters.CharFilter(field_name='cell_measures',
                                              lookup_expr='icontains')

    uid = django_filters.CharFilter(field_name='uid',
                                    lookup_expr='icontains')


class RetrievalRequestFilter(django_filters.FilterSet):
    class Meta:
        models = RetrievalRequest
        fields = ('id', 'requester', 'date_created', 'date_complete',
                  'date_deleted', 'incomplete', 'on_gws', 'finished')

    id = django_filters.NumberFilter(field_name='id')

    requester = django_filters.CharFilter(field_name='requester__username',
                                          lookup_expr='icontains')

    date_time = django_filters.DateFromToRangeFilter(field_name='date_created')

    incomplete = django_filters.NumberFilter(method='filter_incomplete')

    on_gws = django_filters.NumberFilter(method='filter_on_gws')

    finished = django_filters.NumberFilter(method='filter_finished')

    def filter_incomplete(self, queryset, name, value):
        if value:
            return queryset.filter(date_complete__isnull=True)
        return queryset

    def filter_on_gws(self, queryset, name, value):
        if value:
            return queryset.filter(date_complete__isnull=False,
                                   date_deleted__isnull=True)
        return queryset

    def filter_finished(self, queryset, name, value):
        if value:
            return queryset.filter(data_finished=True)
        return queryset


class ReplacedFileFilter(django_filters.FilterSet):
    class Meta:
        model = ReplacedFile
        fields = ('name', 'incoming_directory', 'version', 'tape_url',
                  'institute', 'climate_model', 'experiment', 'mip_table',
                  'rip_code', 'cmor_name', 'grid')

    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='icontains')

    incoming_directory = django_filters.CharFilter(
        field_name='incoming_directory',
        lookup_expr='icontains'
    )

    version = django_filters.CharFilter(field_name='version',
                                        lookup_expr='icontains')

    tape_url = django_filters.CharFilter(field_name='tape_url',
                                         lookup_expr='icontains')

    data_submission = django_filters.NumberFilter(
        field_name='data_submission__id'
    )

    data_request = django_filters.NumberFilter(field_name='data_request__id')

    grid = django_filters.CharFilter(field_name='grid',
                                     lookup_expr='icontains')

    cmor_name = django_filters.CharFilter(
        field_name='variable_request__cmor_name',
        lookup_expr='iexact'
    )

    mip_table = django_filters.CharFilter(
        field_name='variable_request__table_name',
        lookup_expr='iexact'
    )

    institute = django_filters.CharFilter(field_name='institute__short_name',
                                          lookup_expr='icontains')

    climate_model = django_filters.CharFilter(
        field_name='climate_model__short_name',
        lookup_expr='icontains')

    experiment = django_filters.CharFilter(field_name='experiment__short_name',
                                           lookup_expr='icontains')

    rip_code = django_filters.CharFilter(field_name='rip_code',
                                         lookup_expr='icontains')


class ObservationDatasetFilter(django_filters.FilterSet):
    class Meta:
        model = ObservationDataset
        fields = ('name', 'version', 'url', 'summary', 'variables')

    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='icontains')

    version = django_filters.CharFilter(field_name='version',
                                        lookup_expr='icontains')

    url = django_filters.CharFilter(field_name='url',
                                    lookup_expr='icontains')

    summary = django_filters.CharFilter(field_name='summary',
                                        lookup_expr='icontains')

    variables = django_filters.CharFilter(method='variables_filter')

    def variables_filter(self, queryset, name, value):
        return queryset.filter(
            Q(observationfile__standard_name__icontains=value) |
            Q(observationfile__long_name__icontains=value) |
            Q(observationfile__var_name__icontains=value)
        )


class ObservationFileFilter(django_filters.FilterSet):
    class Meta:
        model = ObservationFile
        fields = ('name', 'obs_set_name', 'directory', 'obs_set',
                  'variable_name')

    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='icontains')

    obs_set_name = django_filters.CharFilter(field_name='obs_set__name',
                                             lookup_expr='icontains')

    directory = django_filters.CharFilter(field_name='directory',
                                          lookup_expr='icontains')

    obs_set = django_filters.NumberFilter(field_name='obs_set__id')

    variable_name = django_filters.CharFilter(field_name='variable_name',
                                              lookup_expr='icontains')
