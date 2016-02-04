from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as authviews

admin.autodiscover()

urlpatterns = [
    url(r'^cache/', include('keyedcache.urls')),
    url(r'^accounts/login/', authviews.login, {'template_name': 'admin/login.html'}),
    url(r'^admin/', include(admin.site.urls)),
]
