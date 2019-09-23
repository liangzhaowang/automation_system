from django.conf.urls import url
import views


urlpatterns = [
    url(r'^$', views.index),
    url(r'update_]', views.index),
    url(r'available_products/', views.get_available_products),
]
