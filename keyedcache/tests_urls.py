from django.conf.urls import include, url
from django.contrib import admin
import django.contrib.auth.views

admin.autodiscover()

urlpatterns = [
    url(r'^cache/', include('keyedcache.urls')),
    url(r'^accounts/login/', django.contrib.auth.views.login, {'template_name': 'admin/login.html'}),
    url(r'^admin/', include(admin.site.urls)),
]
