# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import patch
from models import bkc
from models import uploads
# Register your models here.

class patchAdmin(admin.ModelAdmin):
    list_display = ['patch', 'patchtime', 'owner', 'subject', 'status', 'track', 'available','category','project']

class bkcAdmin(admin.ModelAdmin):
    list_display = ['time','eb','sub','project']

class uploadsAdmin(admin.ModelAdmin):
    list_display = ['user','project','build','url']

admin.site.register(patch, patchAdmin)
admin.site.register(bkc, bkcAdmin)
admin.site.register(uploads, uploadsAdmin)
