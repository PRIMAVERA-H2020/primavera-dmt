"""
A custom class for drawing tables from QuerySets

Taken from: http://stackoverflow.com/questions/25256239/\
how-do-i-filter-tables-with-django-generic-views
"""
from __future__ import unicode_literals, division, absolute_import

from django_tables2 import SingleTableView


class PagedFilteredTableView(SingleTableView):
    filter_class = None
    context_filter_name = 'filter'
    page_title = None

    def get_queryset(self, **kwargs):
        qs = super(PagedFilteredTableView, self).get_queryset()
        self.filter = self.filter_class(self.request.GET, queryset=qs)
        return self.filter.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super(PagedFilteredTableView, self).get_context_data()
        context[self.context_filter_name] = self.filter
        context['page_title'] = self.page_title
        return context


class DataRequestsFilteredView(PagedFilteredTableView):
    message = None
    get_outstanding_data = False
    get_received_data = False

    def get_queryset(self, **kwargs):
        qs = super(PagedFilteredTableView, self).get_queryset()
        if self.get_outstanding_data:
            qs = qs.filter(datafile__isnull=True)
        if self.get_received_data:
            qs = qs.filter(datafile__isnull=False)
        self.filter = self.filter_class(self.request.GET, queryset=qs)
        return self.filter.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super(DataRequestsFilteredView, self).get_context_data()
        context['message'] = self.message
        context['get_outstanding_data'] = self.get_outstanding_data
        context['get_received_data'] = self.get_received_data
        return context
