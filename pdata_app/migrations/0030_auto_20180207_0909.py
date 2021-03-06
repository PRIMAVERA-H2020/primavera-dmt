# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-07 09:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pdata_app', '0029_auto_20180206_1048'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationDataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Name')),
                ('version', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Version')),
                ('url', models.URLField(blank=True, null=True, verbose_name=b'URL')),
                ('summary', models.CharField(blank=True, max_length=4000, null=True, verbose_name=b'Summary')),
                ('date_downloaded', models.DateTimeField(blank=True, null=True, verbose_name=b'Date downloaded')),
            ],
            options={
                'verbose_name': 'Observations Dataset',
            },
        ),
        migrations.CreateModel(
            name='ObservationFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name=b'File name')),
                ('incoming_directory', models.CharField(max_length=500, verbose_name=b'File name')),
                ('directory', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'File name')),
                ('tape_url', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Tape URL')),
                ('online', models.BooleanField(default=True, verbose_name=b'Is the file online?')),
                ('size', models.BigIntegerField(verbose_name=b'File size')),
                ('checksum_value', models.CharField(blank=True, max_length=200, null=True)),
                ('checksum_type', models.CharField(blank=True, choices=[(b'SHA256', b'SHA256'), (b'MD5', b'MD5'), (b'ADLER32', b'ADLER32')], max_length=20, null=True)),
                ('start_time', models.FloatField(blank=True, null=True, verbose_name=b'Start time')),
                ('end_time', models.FloatField(blank=True, null=True, verbose_name=b'End time')),
                ('time_units', models.CharField(blank=True, max_length=50, null=True, verbose_name=b'Time units')),
                ('calendar', models.CharField(blank=True, choices=[(b'360_day', b'360_day'), (b'365_day', b'365_day'), (b'gregorian', b'gregorian')], max_length=20, null=True, verbose_name=b'Calendar')),
                ('frequency', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Frequency')),
                ('standard_name', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Standard name')),
                ('long_name', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Long name')),
                ('var_name', models.CharField(blank=True, max_length=30, null=True, verbose_name=b'Var name')),
                ('units', models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Units')),
                ('obs_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pdata_app.ObservationDataset')),
            ],
            options={
                'verbose_name': 'Observations File',
            },
        ),
        migrations.AlterUniqueTogether(
            name='observationdataset',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='observationfile',
            unique_together=set([('name', 'incoming_directory')]),
        ),
    ]
