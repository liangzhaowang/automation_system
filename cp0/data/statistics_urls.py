from django.conf.urls import url, include
import data.statistics as views


urlpatterns = [
    url(r'get/summary/', views.get_summary),
    url(r'get/weekly/(\d+)', views.get_weekly_statistics),
    url(r'get/(\d+)', views.get_statistics),
    url(r'', views.index),
]