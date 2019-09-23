from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class SlaveStatus(object):
    def __init__(self):
        pass


class UserCPZ(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wwid = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.CharField(max_length=8, null=True, blank=True)
    hide_icon = models.BooleanField(default=False)

    def get_avatar(self):
        if self.avatar == None or self.avatar == '':
            return 'default.jpg'
        else:
            return self.avatar


class Message(models.Model):
    user = models.ForeignKey(User)
    content = models.CharField(max_length=500, null=True, blank=True)
    available = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)
    parent_id = models.IntegerField(default=0)
    title = models.CharField(max_length=30, default='', null=True, blank=True)

    def replies(self):
        replies = Message.objects.filter(parent_id=self.id)
        return replies

