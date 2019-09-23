from django.contrib import admin
from home.models import UserCPZ, Message
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Register your models here.
class UserCPZInline(admin.StackedInline):
    model = UserCPZ
    can_delete = False
    verbose_name_plural = 'CP0 User'


class UserAdmin(BaseUserAdmin):
    inlines = (UserCPZInline,)


class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content', 'parent_id']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Message, MessageAdmin)

