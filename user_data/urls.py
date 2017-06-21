from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^$', views.index, name='users_index'),
    url(r'^ebird/$', views.configure_ebird, name='configure_ebird'),
]
