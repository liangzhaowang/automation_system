# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from django.db import models
from django.contrib.auth.models import User

CHOICE = (
    ('cold boot opt','cold boot opt'),
    ('s2r','s2r'),
    ('graphics','graphics'),
    ('wifi','wifi'),
    ('debug only','debug only'),
    ('others' ,'others'),
)

class patch(models.Model):
    name = models.CharField(max_length=30)
    patch = models.CharField(max_length=1000)
    patchtime = models.DateTimeField(auto_now=False)
    owner = models.CharField(max_length=30)
    subject = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    track = models.CharField(max_length=500)
    available = models.NullBooleanField(default=True)
    category = models.CharField(max_length=15,default='',choices=CHOICE)
    comments = models.CharField(max_length=200, default='')
    project = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name
    def shortpatch(self):
        return re.findall(r'/(\d+)',self.patch)[0]
    def fullpatch(self):
        return 'https://android.intel.com/#/c/%s/' % re.findall(r'/(\d+)',self.patch)[0]

class bkc(models.Model):
    time = models.DateTimeField(max_length=100)
    eb = models.CharField(max_length=200)
    sub = models.CharField(max_length=100,default='')
    patchlist = models.CharField(max_length=15000)
    task = models.CharField(max_length=100,default='')
    project = models.CharField(max_length=100)

class uploads(models.Model):
    user = models.ForeignKey(User)
    create_time = models.DateTimeField(auto_now=False)
    project = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    build = models.CharField(max_length=100)
    available = models.NullBooleanField(default=True)
# Create your models here.


