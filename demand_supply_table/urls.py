from django.conf.urls import patterns, url

from demand_supply_table import views

urlpatterns = patterns('',
    url(r'^$', views.ds_table_app, name='ds_table_app'),
)
