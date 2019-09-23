from django.contrib import admin
from .models import Project, TrendsData, BuildPath, Slave, Task, Logger, ConfigTemplate, Production

# Register your models here.


def cancel_task_in_queue(ModelAdmin, request, queryset):
    queryset.update(available=False)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name']


class SlaveAdmin(admin.ModelAdmin):
    list_display = ['num', 'ip', 'user_name', 'ram']


class BuildPathAdmin(admin.ModelAdmin):
    list_display = ['project', 'url', 'buildbot_link', 'build_type']


class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'available', 'test_config', 'submitter', 'test_id', 'create_time', 'end_time', 'slave']
    actions = [cancel_task_in_queue]


class LoggerAdmin(admin.ModelAdmin):
    list_display = ['description', 'user', 'project', 'slave', 'test_config']


class ConfigTemplateAdmin(admin.ModelAdmin):
    list_display = ['user', 'template_name', 'public']


class ProductionAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name']


admin.site.register(Project, ProjectAdmin)
admin.site.register(BuildPath, BuildPathAdmin)
admin.site.register(Slave, SlaveAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Logger, LoggerAdmin)
admin.site.register(ConfigTemplate, ConfigTemplateAdmin)
admin.site.register(Production, ProductionAdmin)
