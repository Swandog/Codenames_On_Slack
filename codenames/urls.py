from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import codenames.views

# Examples:
# url(r'^$', 'codenames.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', codenames.views.index, name='index'),
    url(r'^db', codenames.views.db, name='db'),
    url(r'^admin/', include(admin.site.urls)),
]
