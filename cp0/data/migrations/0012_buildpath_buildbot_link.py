# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-12-12 05:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0011_configtemplate_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildpath',
            name='buildbot_link',
            field=models.URLField(default=''),
            preserve_default=False,
        ),
    ]
