from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^cache/', include('keyedcache.urls')),
    url(r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}),
    url(r'^admin/', include(admin.site.urls)),
)
