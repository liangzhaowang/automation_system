from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Remark(models.Model):
    indicator_id = models.IntegerField()
    content = models.CharField(max_length=100)

class Bug(models.Model):
    indicator_id = models.IntegerField()
    bug_id = models.CharField(max_length=14)

class Mdconfig(models.Model):
    project = models.CharField(max_length=200,primary_key=True)
    device = models.CharField(max_length=200)
    distro = models.CharField(max_length=200)