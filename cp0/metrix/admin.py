from django.contrib import admin
from metrix.models import Mdconfig

# Register your models here.
class Metrix_defaultAdmin(admin.ModelAdmin):
    list_display = ['project','device','distro']

admin.site.register(Mdconfig, Metrix_defaultAdmin)