from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import app.views
import django_slack_oauth

# Examples:
# url(r'^$', 'app.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', app.views.index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^generate_wordset$', app.views.generate_wordset),
    url(r'^initialize_game$', app.views.initialize_game),
    url(r'^slack/', include('django_slack_oauth.urls')),
    url(r'^button/', app.views.button),
    url(r'^close_teams', app.views.close_teams),
    url(r'^test_webhook', app.views.test_webhook),
    url(r'^get_map_card', app.views.show_map_card),
    url(r'^give_hint', app.views.give_hint),
    url(r'^cancel_game', app.views.cancel_game),
    url(r'^current_score', app.views.current_score),
]
