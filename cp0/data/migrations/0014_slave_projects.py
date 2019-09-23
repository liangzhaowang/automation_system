# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2019-03-14 08:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0013_auto_20190130_1548'),
    ]

    operations = [
        migrations.AddField(
            model_name='slave',
            name='projects',
            field=models.ManyToManyField(blank=True, null=True, related_name='project_slave', to='data.Project'),
        ),
    ]
