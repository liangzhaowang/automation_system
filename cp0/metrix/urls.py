from django.conf.urls import url

import views as metrix_views

urlpatterns = [
    # Metrix
    url(r'^metrix/$', metrix_views.metrix_index),
    url(r'^metrix/data/$', metrix_views.metrix_data),
    url(r'^metrix/examp/(.+)/$', metrix_views.examp),
    url(r'^metrix/jira_raw_data/(.+)/$', metrix_views.get_jira_raw_data),
    url(r'^metrix/examp_templates/(.+).html$', metrix_views.examp_templates),
    url(r'^metrix/get_dedualt_config/$',metrix_views.Metrix_Defualt_Config),
]