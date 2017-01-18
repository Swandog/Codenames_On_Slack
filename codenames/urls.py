from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import app.views

# Examples:
# url(r'^$', 'app.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', app.views.index, name='index'),
    url(r'^db', app.views.db, name='db'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^generate_wordset$', app.views.generate_wordset),
    url(r'^initialize_game$', app.views.initialize_game),
    url(r'^slack/', include('django_slack_oauth.urls')),
    url(r'^button/', app.views.button),
    url(r'^close_teams', app.views.close_teams),
    url(r'^test_webhook', app.views.test_webhook),
    url(r'^reveal_map_to_red_spymaster', app.views.reveal_map_to_red_spymaster),
]
