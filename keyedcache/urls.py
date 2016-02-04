"""
URLConf for Caching app
"""

from django.conf.urls import url
from keyedcache import views

urlpatterns = [
    url(r'^$', views.stats_page, {}, 'keyedcache_stats'),
    url(r'^view/$', views.view_page, {}, 'keyedcache_view'),
    url(r'^delete/$', views.delete_page, {}, 'keyedcache_delete'),
]
