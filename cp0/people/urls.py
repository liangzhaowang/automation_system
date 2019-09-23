from django.conf.urls import url
from people import views as people_views

urlpatterns = [
    url(r'^patch/(.+)/$', people_views.index_page),
    url(r'^select/(.+)/$',people_views.select_page),
    url(r'^delete/(.+)/$',people_views.del_page),
    url(r'^test/(.+)/$', people_views.test_page),
    url(r'^calendar_data/(.+)/$',people_views.calendar_data_page),
    url(r'^calendar/(.+)/$',people_views.calendar_page),
    url(r'^week/(.+)/$',people_views.week_page),
    url(r'^view_attachment/(.+)$',people_views.view_attach),
    url(r'^view_log/(.+)/$',people_views.view_log),
    url(r'^down_log/(.+)/$',people_views.download_log),
    url(r'^Get_list/', people_views.Get_list),
    url(r'^upload_file/', people_views.upload_file),
    url(r'^create_file/', people_views.create_file),
    url(r'^addmerged/', people_views.addmerge_page),
    url(r'^generate_build/(.+)/', people_views.generate_build),
    url(r'^patches/(.+)/', people_views.getpatches)
]