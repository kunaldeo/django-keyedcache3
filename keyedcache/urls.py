"""
URLConf for Caching app
"""

try:
	from django.conf.urls import patterns
except ImportError:
	from django.conf.urls.defaults import patterns


urlpatterns = patterns('keyedcache.views',
    (r'^$', 'stats_page', {}, 'keyedcache_stats'),
    (r'^view/$', 'view_page', {}, 'keyedcache_view'),
    (r'^delete/$', 'delete_page', {}, 'keyedcache_delete'),
)
