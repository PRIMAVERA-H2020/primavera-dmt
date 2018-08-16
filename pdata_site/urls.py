from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from pdata_app.forms import SetPasswordBootstrapForm
import pdata_app.views

from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^login/$', pdata_app.views.view_login, name='login'),

    url(r'^logout/$', pdata_app.views.view_logout, name='logout'),

    url(r'^password_change/$', pdata_app.views.view_change_password,
        name='password_change'),

    url(r'^password_change/done/$',
        pdata_app.views.view_change_password_success,
        name='password_change_done'),

    url(r'^register/$', pdata_app.views.view_register,
        name='register'),

    url(r'^register/done/$', pdata_app.views.view_register_success,
        name='register_success'),

    url(r'^register/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-'
        r'[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {'post_reset_redirect': 'register_complete',
         'template_name': 'pdata_app/register_user_confirm.html',
         'set_password_form': SetPasswordBootstrapForm},
        name='password_reset_confirm'),

    url(r'^register/complete/$', auth_views.password_reset_complete, {
        'template_name': 'pdata_app/register_user_done.html',
    }, name='register_complete'),

    url(r'^files/$', pdata_app.views.DataFileList.as_view(), name='data_files'),

    url(r'^replaced_files/$', pdata_app.views.ReplacedFileList.as_view(),
        name='replaced_files'),

    url(r'^submissions/$', pdata_app.views.DataSubmissionList.as_view(),
        name='data_submissions'),

    url(r'^esgf_datasets/$', pdata_app.views.ESGFDatasetList.as_view(),
        name='esgf_datasets'),

    url(r'^ceda_datasets/$', pdata_app.views.CEDADatasetList.as_view(),
        name='ceda_datasets'),

    url(r'^data_requests/$', pdata_app.views.DataRequestList.as_view(),
        name='data_requests'),

    url(r'^outstanding_data/$',
        pdata_app.views.OutstandingDataRequestList.as_view(),
        name='outstanding_data'),

    url(r'^received_data/$',
        pdata_app.views.ReceivedDataRequestList.as_view(),
        name='received_data'),

    url(r'^received_data_quick_query/$',
        pdata_app.views.view_received_quick_query,
        name='received_data_quick_query'),

    url(r'^data_issues/$', pdata_app.views.DataIssueList.as_view(),
        name='data_issues'),

    url(r'^variable_requests/$',
        pdata_app.views.VariableRequestList.as_view(),
        name='variable_requests'),

    url(r'^create_submission/$', pdata_app.views.create_submission,
        name='create_submission'),

    url(r'^retrieval_requests/$',
        pdata_app.views.RetrievalRequestList.as_view(),
        name='retrieval_requests'),

    url(r'^retrieval_years/$', pdata_app.views.retrieval_years,
        name='retrieval_years'),

    url(r'^confirm_retrieval/$', pdata_app.views.confirm_retrieval,
        name='confirm_retrieval'),

    url(r'^create_retrieval/$', pdata_app.views.create_retrieval,
        name='create_retrieval'),

    url(r'confirm_mark_finished', pdata_app.views.confirm_mark_finished,
        name='confirm_mark_finished'),

    url(r'^mark_finished/$', pdata_app.views.mark_finished,
        name='mark_finished'),

    url(r'^observation_sets/$',
        pdata_app.views.ObservationDatasetList.as_view(), name='obs_sets'),

    url(r'^observation_files/$',
        pdata_app.views.ObservationFileList.as_view(), name='obs_files'),

    url(r'.*', pdata_app.views.view_home, name='home'),
]

urlpatterns += staticfiles_urlpatterns()
