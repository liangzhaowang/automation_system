from django.conf.urls import url
from home import workspace
import views
import tasks
import profile
import mytask


def error(request):
    return ''


urlpatterns = [
    url(r'accounts/login/', views.login_view),
    url(r'accounts/register/', views.register_view),
    url(r'accounts/case/', views.add_case),
    url(r'accounts/slave_info/', views.get_slaveProject),
    url(r'accounts/save_case/', views.save_case),
    url(r'accounts/logout/', views.logout),
    url(r'accounts/workspace/slave/(\d+)', workspace.slave),
    url(r'accounts/workspace/create_project/', workspace.create_project),
    url(r'accounts/workspace/', workspace.index),
    url(r'accounts/get_contributors/', workspace.get_contributors),
    url(r'dashboard/', profile.profile_view),
    url(r'accounts/mytasks/', mytask.mytask_view),
    url(r'accounts/getmytasks/', mytask.getmytask),
    url(r'accounts/getmyfavorites/', mytask.getmyfavorites),
    url(r'accounts/getmymanualtasks/', mytask.getmymanualtasks),
    url(r'add_slave/', profile.add_slave),
    url(r'update_slave/(\d+)/', profile.update_slave),
    url(r'^history/(.+)/$', views.history),
    url(r'releases/$', views.releases),
    url(r'new/$', views.new_test),
    url(r'new/slave/(.+)$', views.add_test),
    url(r'new/(.+)$', views.copy_test),
    url(r'tasks/$', tasks.index),
    url(r'sso/$', views.sso),
    url(r'error/$', error),
    url(r'^$', views.index),

]

handler404 = views.page_not_found
handler500 = views.page_error
