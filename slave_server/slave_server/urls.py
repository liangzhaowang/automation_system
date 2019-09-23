"""slave_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
import api
# from django.contrib import admin

urlpatterns = [
    url(r'^$', api.hello),
    url(r'^test_cases/(.+)/$', api.test_cases),
    url(r'^test/$', api.test),
    url(r'^stat/$', api.status),
    url(r'^slave_stat/$', api.slave_stat),
    url(r'^reset/$', api.reset),
    url(r'^progress/$', api.progress),
    url(r'^update_slave/$', api.update_slave),
    url(r'^get_testing_task_total_est/$', api.get_testing_task_total_est),
    url(r'^add_case/$', api.add_case)
]
