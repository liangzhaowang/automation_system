from django.conf.urls import url, include
import bisects.views as bisects_views
import views
import api
import charts
import attachment_views.stack_bar

urlpatterns = [
    url(r'accounts/template/', views.test_template_index),
    url(r'production/(.+)/$', views.production_index),
    url(r'project/active/$', api.active_project),
    url(r'project/(.+)/$', views.view_project),
    # url(r'project/$', views.project_index),
    url(r'bkc/(.+)/([0-9]{4})/(.+)/$', views.bkc),
    url(r'bkc/(.+)/$', views.bkc),
    url(r'daily/(.+)/(.+)/bisects/create/$', bisects_views.create),
    url(r'daily/(.+)/(.+)/bisects/view/$', bisects_views.view),
    url(r'daily/(.+)/(.+)/bisects/$', bisects_views.index),
    url(r'daily/(.+)/(.+)/$', views.daily),
    url(r'daily/(.+)/$', views.daily),
    url(r'raw/(.+)/(.+)/(.+)/$', views.raw),
    url(r'raw/(.+)/(.+)/$', views.raw),
    url(r'statistics/', include('data.statistics_urls')),
    url(r'^compare/$', views.compare),
    url(r'^upload_aic/$', views.upload_aicData),

    # Charts
    url(r'^chart_data/(.+)/(.+)/(.+)/(.+)/(.+)/(.+)/$', charts.chart_data),
    url(r'^chart/(.+)/(.+)/(.+)/(.+)/(.+)/(.+)/$', charts.chart),
    url(r'^aic_static/(.+)/(.+)/(.+)/(.+)/(.+)/(.+)/$', charts.chart),

    # Attachments
    url(r'^attachment/(.+)/(.+)/(.+)/(.+)/(.+)/$', views.attachments),
    url(r'^download/attachment/(.+)/(.+)/(.+)/(.+)/(.+)/$', views.download_attachment),

    url(r'^chart/comparision/$', attachment_views.stack_bar.comparision),
    url(r'test_cases/(.+)/(.+)/$', views.test_cases),
    url(r'^api/auth_header', api.auth_header_api),
    url(r'^api/trend/(.+)/(.+)/(.+)/', api.trends),
    url(r'^api/build_path/(.+)/', api.build_paths),
    url(r'^api/build_list/', api.fetch_build_path),
    url(r'^api/target_list/', api.fetch_target),
    url(r'^api/config/(.+)/', api.test_config),
    url(r'^api/task/test_id/', api.update_test_id),
    url(r'^api/trend/(.+)/(.+)/$', api.trends),
    url(r'^api/progress/(.+)/', api.progress),
    url(r'^api/cancel/(.+)/', api.cancel),
    url(r'^api/test_failed/(.+)/(.+)/', api.test_failed),
    url(r'^api/slaves/', api.slave_stat),
    url(r'^api/data_maker/', api.data_maker),
    url(r'^api/add_to_compare_list/', api.add_to_compare_list),
    url(r'^api/clear_compare_list/', api.clear_compare_list),
    url(r'^api/broadcast/', api.broadcast),
    url(r'^api/add_comment', api.add_comment),
    url(r'^api/test_connect', api.test_connect),
    url(r'^api/check_slave_install_status', api.check_slave_install_status),
    url(r'^api/update_slaveserver', api.update_slaveserver),

    # upload
    url(r'^api/test_result$', api.test_result),
    url(r'^api/test_attachment$', api.test_attachment),

    # download
    url(r'^api/download_daily_excel/(.+)/(.+)/$', api.download_daily_excel),
    url(r'^api/download_eb_excel/(.+)/(.+)/$', api.download_eb_excel),

    # history
    url(r'^api/history/(.+)/(.+)/builds/$', api.history_builds_tag),
    url(r'^api/history/(.+)/builds/$', api.history_builds),
    url(r'^api/history/(.+)/(.+)/tests$', api.history_tests),

    # test config
    url(r'^api/show_config/(.+)$', views.get_config),

    # retest
    url(r'^api/retest/$', api.retest),
    url(r'^api/autotest/$', api.autotest),
    url(r'^api/favorite/$', api.favorite),
    url(r'^api/unfavorite/$', api.unfavorite),
    url(r'^api/remove/$', api.remove),
    
    # customize tag
    url(r'^(.+)/(.+)/(.+)/$', views.customize),

    # pca test_tag
    url(r'^pca_test_tag/addFromCustom/$', views.add_test_tag),

    # slave
    url(r'^api/slave/(.+)/(.+)$', api.slave_status),

    # test template
    url(r'^api/test_template/(.+)$', api.get_test_template),

    #convert daily or bkc
    url(r'^api/convert$',api.convert_testdata),

    #remove daily data
    url(r'^api/remove_data/$', api.remove_convert_data),

    #get_data from mongodb
    url(r'^api/get_data/$', api.get_weekly_from_db)
]

handler404 = views.page_not_found
handler500 = views.page_error
