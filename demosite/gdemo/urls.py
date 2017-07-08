from django.conf.urls import url

from . import views

app_name = 'gdemo'

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^main/$', views.main, name='main'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^project$', views.gproject, name='gproject'),
    url(r'^deploy/$', views.ddeploy, name='ddeploy'),
#    url(r'^deployback/$', views.ddeployback, name='ddeployback')
]