from django.conf.urls import url
import views as pca_views

urlpatterns = [
    # rawdata_pca
    url(r'^pca/$', pca_views.pca_index),
    url(r'^pca/casedata/$', pca_views.pca_data),
    url(r'^pca/valdata/$', pca_views.pca_val_data),
    url(r'^pca/charts/$', pca_views.pca_data_chart),
    url(r'^pca/chartsmodify/$', pca_views.pca_modify_data_configuration),
]