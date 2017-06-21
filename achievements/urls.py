from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.AchievementProgressList.as_view(), name='progress_list'),
]
