# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CEDADataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('catalogue_url', models.URLField(verbose_name=b'CEDA Catalogue URL')),
                ('directory', models.CharField(max_length=500, verbose_name=b'Directory')),
                ('doi', models.URLField(null=True, verbose_name=b'DOI', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Checksum',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('checksum_value', models.CharField(max_length=200)),
                ('checksum_type', models.CharField(max_length=6, choices=[(b'SHA256', b'SHA256'), (b'MD5', b'MD5')])),
            ],
        ),
        migrations.CreateModel(
            name='ClimateModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='DataFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'File name')),
                ('incoming_directory', models.CharField(max_length=500, verbose_name=b'Incoming directory')),
                ('directory', models.CharField(max_length=500, verbose_name=b'Current directory')),
                ('size', models.BigIntegerField(verbose_name=b'File size (bytes)')),
                ('frequency', models.CharField(max_length=20, verbose_name=b'Time frequency', choices=[(b'ann', b'ann'), (b'mon', b'mon'), (b'day', b'day'), (b'6hr', b'6hr'), (b'3hr', b'3hr')])),
                ('start_time', models.DateTimeField(null=True, verbose_name=b'Start time', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name=b'End time', blank=True)),
                ('ceda_download_url', models.URLField(null=True, verbose_name=b'CEDA Download URL', blank=True)),
                ('ceda_opendap_url', models.URLField(null=True, verbose_name=b'CEDA OpenDAP URL', blank=True)),
                ('esgf_download_url', models.URLField(null=True, verbose_name=b'ESGF Download URL', blank=True)),
                ('esgf_opendap_url', models.URLField(null=True, verbose_name=b'ESGF OpenDAP URL', blank=True)),
                ('online', models.BooleanField(default=True, verbose_name=b'Is the file online?')),
                ('tape_url', models.URLField(null=True, verbose_name=b'Tape URL', blank=True)),
                ('ceda_dataset', models.ForeignKey(blank=True, to='pdata_app.CEDADataset', null=True)),
                ('climate_model', models.ForeignKey(to='pdata_app.ClimateModel')),
            ],
            options={
                'verbose_name': 'Data File',
            },
        ),
        migrations.CreateModel(
            name='DataIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('issue', models.CharField(max_length=500, verbose_name=b'Issue reported')),
                ('reporter', models.CharField(max_length=60, verbose_name=b'Reporter')),
                ('date_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'Date and time of report')),
                ('data_file', models.ManyToManyField(to='pdata_app.DataFile')),
            ],
        ),
        migrations.CreateModel(
            name='DataRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('frequency', models.CharField(max_length=20, verbose_name=b'Time frequency', choices=[(b'ann', b'ann'), (b'mon', b'mon'), (b'day', b'day'), (b'6hr', b'6hr'), (b'3hr', b'3hr')])),
                ('start_time', models.DateTimeField(verbose_name=b'Start time')),
                ('end_time', models.DateTimeField(verbose_name=b'End time')),
                ('climate_model', models.ForeignKey(to='pdata_app.ClimateModel')),
            ],
        ),
        migrations.CreateModel(
            name='DataSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'EXPECTED', max_length=20, verbose_name=b'Status', choices=[(b'EXPECTED', b'EXPECTED'), (b'ARRIVED', b'ARRIVED'), (b'VALIDATED', b'VALIDATED'), (b'ARCHIVED', b'ARCHIVED'), (b'PUBLISHED', b'PUBLISHED')])),
                ('incoming_directory', models.CharField(max_length=500, verbose_name=b'Incoming Directory')),
                ('directory', models.CharField(max_length=500, verbose_name=b'Main Directory')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ESGFDataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('drs_id', models.CharField(max_length=500, verbose_name=b'DRS Dataset Identifier')),
                ('version', models.CharField(max_length=20, verbose_name=b'Version')),
                ('directory', models.CharField(max_length=500, verbose_name=b'Directory')),
                ('thredds_url', models.URLField(null=True, verbose_name=b'THREDDS Download URL', blank=True)),
                ('ceda_dataset', models.ForeignKey(blank=True, to='pdata_app.CEDADataset', null=True)),
            ],
            options={
                'verbose_name': 'ESGF Dataset',
            },
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='Institute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_paused', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Settings',
            },
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('var_id', models.CharField(max_length=100, verbose_name=b'Variable Id')),
                ('units', models.CharField(max_length=100, verbose_name=b'Units')),
                ('long_name', models.CharField(max_length=100, null=True, verbose_name=b'Long Name', blank=True)),
                ('standard_name', models.CharField(max_length=100, null=True, verbose_name=b'CF Standard Name', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='datarequest',
            name='experiment',
            field=models.ForeignKey(to='pdata_app.Experiment'),
        ),
        migrations.AddField(
            model_name='datarequest',
            name='institute',
            field=models.ForeignKey(to='pdata_app.Institute'),
        ),
        migrations.AddField(
            model_name='datarequest',
            name='variable',
            field=models.ForeignKey(to='pdata_app.Variable'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='data_submission',
            field=models.ForeignKey(to='pdata_app.DataSubmission'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='esgf_dataset',
            field=models.ForeignKey(blank=True, to='pdata_app.ESGFDataset', null=True),
        ),
        migrations.AddField(
            model_name='datafile',
            name='experiment',
            field=models.ForeignKey(to='pdata_app.Experiment'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='project',
            field=models.ForeignKey(to='pdata_app.Project'),
        ),
        migrations.AddField(
            model_name='datafile',
            name='variable',
            field=models.ForeignKey(to='pdata_app.Variable'),
        ),
        migrations.AddField(
            model_name='checksum',
            name='data_file',
            field=models.ForeignKey(to='pdata_app.DataFile'),
        ),
        migrations.AlterUniqueTogether(
            name='esgfdataset',
            unique_together=set([('drs_id', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='datafile',
            unique_together=set([('name', 'directory')]),
        ),
    ]