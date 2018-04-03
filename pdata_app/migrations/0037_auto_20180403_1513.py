# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-03 15:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pdata_app', '0036_auto_20180221_1608'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='esgfdataset',
            name='data_submission',
        ),
        migrations.AddField(
            model_name='esgfdataset',
            name='data_request',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, to='pdata_app.DataRequest', verbose_name=b'Data Request'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='esgfdataset',
            name='status',
            field=models.CharField(choices=[(b'CREATED', b'CREATED'), (b'SUBMITTED', b'SUBMITTED'), (b'AT_CEDA', b'AT_CEDA'), (b'PUBLISHED', b'PUBLISHED'), (b'REJECTED', b'REJECTED'), (b'NEEDS_FIX', b'NEEDS_FIX'), (b'FILES_MISSING', b'FILES_MISSING')], default=b'CREATED', max_length=20, verbose_name=b'Status'),
        ),
        migrations.AlterField(
            model_name='esgfdataset',
            name='directory',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name=b'Directory'),
        ),
    ]
