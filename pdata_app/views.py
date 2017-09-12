import os
import re
import urllib

from django.contrib.auth import (authenticate, login, logout,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Max, Min, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from .models import (DataFile, DataSubmission, ESGFDataset, CEDADataset,
                     DataRequest, DataIssue, VariableRequest, RetrievalRequest)
from .forms import (CreateSubmissionForm, PasswordChangeBootstrapForm,
                    UserBootstrapForm)
from .tables import (DataRequestTable, DataFileTable, DataSubmissionTable,
                     ESGFDatasetTable, CEDADatasetTable, DataIssueTable,
                     VariableRequestQueryTable, DataReceivedTable,
                     RetrievalRequestTable)
from .filters import (DataRequestFilter, DataFileFilter, DataSubmissionFilter,
                      ESGFDatasetFilter, CEDADatasetFilter, DataIssueFilter,
                      VariableRequestQueryFilter, RetrievalRequestFilter)
from .utils.table_views import PagedFilteredTableView, DataRequestsFilteredView
from vocabs.vocabs import STATUS_VALUES


class DataRequestList(DataRequestsFilteredView):
    model = DataRequest
    table_class = DataRequestTable
    filter_class = DataRequestFilter
    page_title = 'Data Requests'
    message = 'These are the data requests made...'


class OutstandingDataRequestList(DataRequestsFilteredView):
    model = DataRequest
    table_class = DataRequestTable
    filter_class = DataRequestFilter
    page_title = 'Outstanding Data Requests'
    get_outstanding_data = True
    message = ('No files have been received for the data requests below. '
               'Please note that this is only a list of the data requests '
               'that no data at all has been received for. The absence of a '
               'data request from this list does not mean that all years '
               'have been received yet.')


class ReceivedDataRequestList(DataRequestsFilteredView):
    model = DataRequest
    table_class = DataReceivedTable
    filter_class = DataRequestFilter
    page_title = 'Variables Received'
    get_received_data = True
    message = 'The following data has been received:'


class VariableRequestList(PagedFilteredTableView):
    model = VariableRequest
    table_class = VariableRequestQueryTable
    filter_class = VariableRequestQueryFilter
    page_title = 'Variable Request'


class DataFileList(PagedFilteredTableView):
    model = DataFile
    table_class = DataFileTable
    filter_class = DataFileFilter
    page_title = 'Data Files'


class DataSubmissionList(PagedFilteredTableView):
    model = DataSubmission
    table_class = DataSubmissionTable
    filter_class = DataSubmissionFilter
    page_title = 'Data Submissions'


class ESGFDatasetList(PagedFilteredTableView):
    model = ESGFDataset
    table_class = ESGFDatasetTable
    filter_class = ESGFDatasetFilter
    page_title = 'ESGF Datasets'


class CEDADatasetList(PagedFilteredTableView):
    model = CEDADataset
    table_class = CEDADatasetTable
    filter_class = CEDADatasetFilter
    page_title = 'CEDA Datasets'


class DataIssueList(PagedFilteredTableView):
    model = DataIssue
    table_class = DataIssueTable
    filter_class = DataIssueFilter
    page_title = 'Data Issues'


class RetrievalRequestList(PagedFilteredTableView):
    model = RetrievalRequest
    table_class = RetrievalRequestTable
    filter_class = RetrievalRequestFilter
    page_title = 'Retrieval Requests'


def view_login(request):
    if request.method == 'GET':
        next_page = request.GET.get('next')
        if next_page:
            return render(request, 'pdata_app/login.html', {'request': request,
                'page_title': 'Login', 'next': next_page})
        else:
            return render(request, 'pdata_app/login.html', {'request': request,
                'page_title': 'Login'})

    username = request.POST['username']
    password = request.POST['password']
    next_page = request.POST['next']
    user = authenticate(username=username, password=password)
    if user is not None and user.is_active:
        login(request, user)
        if next_page:
            return redirect(next_page)
        else:
            return redirect('home')
    else:
        if next_page:
            return render(request, 'pdata_app/login.html', {'request': request,
                'page_title': 'Login', 'next': next_page, 'errors': True})
        else:
            return render(request, 'pdata_app/login.html', {'request': request,
                'page_title': 'Login', 'errors': True})


def view_logout(request):
    logout(request)
    return redirect('home')


@login_required(login_url='/login/')
def view_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeBootstrapForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return redirect('password_change_done')
    else:
        form = PasswordChangeBootstrapForm(request.user)
    return render(request, 'pdata_app/generic_form.html',
                  {'form': form, 'page_title': 'Change Password'})


def view_change_password_success(request):
    return render(request, 'pdata_app/password_change_success.html',
                  {'request': request, 'page_title': 'Change Password'})


def view_register(request):
    if request.method == 'POST':
        user_form = UserBootstrapForm(data=request.POST)
        if user_form.is_valid():
            # check to see if this email address is unique
            if User.objects.filter(email=request.POST['email']):
                user_form.add_error('email', 'A user with that email address '
                                             'already exists.')
                return render(request, 'pdata_app/generic_form.html',
                              {'form': user_form,
                               'page_title': 'Create Account'})

            # Create a database object from the user's form data
            user = user_form.save(commit=False)

            # Set a random password so that the email address can be verified
            user.set_password(User.objects.make_random_password())
            user.save()

            # This form only requires the "email" field, so will validate.
            reset_form = PasswordResetForm(request.POST)
            reset_form.is_valid()  # Must trigger validation
            # Copied from django/contrib/auth/views.py : password_reset
            opts = {
                'use_https': True,
                'email_template_name':
                    'pdata_app/register_user_email_message.html',
                'subject_template_name':
                    'pdata_app/register_user_email_subject.html',
                'request': request,
                'from_email': 'no-reply@prima-dm.ceda.ac.uk'
            }
            # This form sends the email on save()
            reset_form.save(**opts)

            return redirect('register_success')
    else:
        user_form = UserBootstrapForm()

    # Render the template depending on the context.
    return render(request, 'pdata_app/generic_form.html',
            {'form': user_form, 'page_title': 'Create Account'})


def view_register_success(request):
    return render(request, 'pdata_app/register_user_success.html',
                  {'request': request, 'page_title': 'Create Account'})


def view_home(request):
    return render(request, 'pdata_app/home.html',
                  {'request': request, 'page_title': 'The PRIMAVERA DMT'})


@login_required(login_url='/login/')
def create_submission(request):
    if request.method == 'POST':
        form = CreateSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.incoming_directory = os.path.normpath(
                submission.incoming_directory)
            submission.directory = submission.incoming_directory
            submission.status = STATUS_VALUES['PENDING_PROCESSING']
            submission.user = request.user
            submission.save()
            return _custom_redirect('data_submissions')
    else:
        form = CreateSubmissionForm()
    return render(request, 'pdata_app/create_submission_form.html',
                  {'form': form,
                   'page_title': 'Create Data Submission'})


@login_required(login_url='/login/')
def retrieval_years(request):
    if request.method == 'POST':
        data_req_ids = []
        # loop through the items in the POST from the form and identify any
        # DataRequest object ids that have been requested
        for key in request.POST:
            components = re.match(r'^request_data_req_(\d+)$', key)
            if components:
                data_req_ids.append(int(components.group(1)))
        # get a string representation of each id
        # TODO what if id doesn't exist?
        data_req_strs = [str(DataRequest.objects.filter(id=req).first())
                         for req in data_req_ids]

        earliest_year = min([DataRequest.objects.get(id=req).
                            datafile_set.aggregate(
                            Min('start_time'))['start_time__min']
                            for req in data_req_ids])
        latest_year = max([DataRequest.objects.get(id=req).
                           datafile_set.aggregate(
                           Max('end_time'))['end_time__max']
                           for req in data_req_ids])
        # generate the confirmation page
        return render(request, 'pdata_app/retrieval_request_confirm.html',
                      {'request': request, 'data_reqs':data_req_strs,
                       'page_title': 'Confirm Retrieval Request',
                       'return_url': request.POST['variables_received_url'],
                       'data_request_ids': ','.join(map(str, data_req_ids)),
                       'earliest_year': earliest_year,
                       'latest_year': latest_year})
    else:
        # TODO do something intelligent
        return render(request, 'pdata_app/retrieval_request_error.html',
                      {'request': request,
                       'page_title': 'Retrieval Request'})


@login_required(login_url='/login/')
def confirm_retrieval(request):
    if request.method == 'POST':
        data_req_ids = []
        # loop through the items in the POST from the form and identify any
        # DataRequest object ids that have been requested
        for key in request.POST:
            components = re.match(r'^request_data_req_(\d+)$', key)
            if components:
                data_req_ids.append(int(components.group(1)))
        # get a string representation of each id
        # TODO what if id doesn't exist?
        data_req_strs = [str(DataRequest.objects.filter(id=req).first())
                         for req in data_req_ids]
        # get the total size of the retrieval request
        request_size = sum([DataRequest.objects.get(id=req).
                            datafile_set.aggregate(Sum('size'))['size__sum']
                            for req in data_req_ids])
        # generate the confirmation page
        return render(request, 'pdata_app/retrieval_request_confirm.html',
                      {'request': request, 'data_reqs':data_req_strs,
                       'page_title': 'Confirm Retrieval Request',
                       'return_url': request.POST['variables_received_url'],
                       'data_request_ids': ','.join(map(str, data_req_ids)),
                       'request_size': request_size})
    else:
        # TODO do something intelligent
        return render(request, 'pdata_app/retrieval_request_error.html',
                      {'request': request,
                       'page_title': 'Retrieval Request'})


@login_required(login_url='/login/')
def create_retrieval(request):
    if request.method == 'POST':
        # create the request
        retrieval = RetrievalRequest.objects.create(requester=request.user)
        retrieval.save()
        # add the data requests asked for
        data_req_ids = [int(req_id) for req_id in
                        request.POST['data_request_ids'].split(',')]
        data_reqs = DataRequest.objects.filter(id__in=data_req_ids)
        retrieval.data_request.add(*data_reqs)
        retrieval.save()
        # redirect to the retrieval just created
        return _custom_redirect('retrieval_requests')
    else:
        return render(request, 'pdata_app/retrieval_request_error.html',
                      {'request': request,
                       'page_title': 'Retrieval Request'})


@login_required(login_url='/login/')
def confirm_mark_finished(request):
    if request.method == 'POST':
        ret_req_ids = []
        # loop through the items in the POST from the form and identify any
        # RetrievalRequest object ids that have been specified
        for key in request.POST:
            components = re.match(r'^finished_ret_req_(\d+)$', key)
            if components:
                ret_req_ids.append(int(components.group(1)))

        # get a summary of each return request
        # TODO what if id doesn't exist?
        ret_req_summaries = []
        for req in ret_req_ids:
            summary = {}
            summary['id'] = req
            ret_req = RetrievalRequest.objects.get(id=req)
            summary['data_reqs'] = [str(data_req) for data_req in
                                    ret_req.data_request.all()]
            summary['size'] = (ret_req.data_request.all().
                               aggregate(Sum('datafile__size'))
                               ['datafile__size__sum'])
            ret_req_summaries.append(summary)


        # generate the confirmation page
        return render(request, 'pdata_app/mark_finished_confirm.html',
                      {'request': request,
                       'ret_req_summaries': ret_req_summaries,
                       'page_title': 'Confirm Mark Retrievals Finished',
                       'return_url': request.POST['retrieval_requests_url'],
                       'ret_request_ids': ','.join(map(str, ret_req_ids)),
                       'total_size':sum([summary['size']
                                         for summary in ret_req_summaries])})
    else:
        # TODO do something intelligent
        return render(request, 'pdata_app/mark_finished_error.html',
                      {'request': request,
                       'page_title': 'Retrieval Request'})


@login_required(login_url='/login/')
def mark_finished(request):
    if request.method == 'POST':
        # mark the return requests asked for
        ret_req_ids = [int(req_id) for req_id in
                        request.POST['ret_request_ids'].split(',')]
        for ret_req_id in ret_req_ids:
            ret_req = RetrievalRequest.objects.get(id=ret_req_id)
            ret_req.data_finished = True
            ret_req.save()
        return _custom_redirect('retrieval_requests')
    else:
        return render(request, 'pdata_app/mark_finished_error.html',
                      {'request': request,
                       'page_title': 'Retrieval Request'})


def _custom_redirect(url_name, *args, **kwargs):
    """
    Generate an HTTP redirect to URL with GET parameters.

    For example: _custom_redirect('data_submissions', sort='-date_submitted')
    should redirect to data_submissions/?sort=-date_submitted

    From: http://stackoverflow.com/a/3766452

    :param str url_name:
    :param str args:
    :param kwargs:
    :return: An HTTP response
    """
    url = reverse(url_name, args=args)
    params = urllib.urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)
