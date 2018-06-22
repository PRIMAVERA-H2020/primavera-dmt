from __future__ import unicode_literals, division, absolute_import
from django.contrib import admin
from solo.admin import SingletonModelAdmin

from pdata_app.models import *
from pdata_app.models import model_names


class DataFileInline(admin.TabularInline):
    fields = ('name', 'directory')
    model = DataFile
    extra = 1

class DataIssueInline(admin.TabularInline):
    model = DataIssue
    extra = 1

class DataSubmissionAdmin(admin.ModelAdmin):
    inlines = [DataFileInline]
    save_on_top = True

# Registering models to have admin forms
admin.site.register(DataSubmission, DataSubmissionAdmin)
admin.site.register(Settings, SingletonModelAdmin)

for model_name in model_names:
    if model_name in ("Settings", "DataSubmission"): continue
    admin.site.register(eval(model_name))
