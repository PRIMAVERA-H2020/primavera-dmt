# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-19 17:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdata_app', '0040_auto_20181101_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='esgfdataset',
            name='status',
            field=models.CharField(choices=[(b'CREATED', b'CREATED'), (b'SUBMITTED', b'SUBMITTED'), (b'SUBMIT_FAILED', b'SUBMIT_FAILED'), (b'AT_CEDA', b'AT_CEDA'), (b'PUBLISHED', b'PUBLISHED'), (b'REJECTED', b'REJECTED'), (b'NEEDS_FIX', b'NEEDS_FIX'), (b'FILES_MISSING', b'FILES_MISSING'), (b'NOT_ON_DISK', b'NOT_ON_DISK'), (b'MULTIPLE_DIRECTORIES', b'MULTIPLE_DIRECTORIES')], default=b'CREATED', max_length=20, verbose_name='Status'),
        ),
    ]
