# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-10-22 06:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0006_auto_20180918_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='start_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='end_time',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]