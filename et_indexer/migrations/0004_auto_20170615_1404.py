# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-06-15 14:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('et_indexer', '0003_auto_20170615_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file_size',
            field=models.BigIntegerField(verbose_name='File Size'),
        ),
    ]