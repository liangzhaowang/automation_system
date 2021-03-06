# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2019-01-30 07:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_buildpath_buildbot_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='Production',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('short_name', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='production',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='data.Production'),
        ),
    ]
