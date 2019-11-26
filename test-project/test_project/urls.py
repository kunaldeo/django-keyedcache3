from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import LoginView

admin.autodiscover()

urlpatterns = [
    url(r'^cache/', include('keyedcache.urls')),
    url(r'^accounts/login/$', LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^admin/', admin.site.urls),
]
