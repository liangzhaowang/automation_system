# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-09-26 05:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_delete_bxtp_evs'),
    ]

    operations = [
        migrations.DeleteModel(
            name='bkc',
        ),
        migrations.DeleteModel(
            name='patch',
        ),
    ]
