# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-24 16:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pdata_app', '0015_auto_20170223_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataissue',
            name='reporter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name=b'Reporter'),
        ),
    ]
