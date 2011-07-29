from django.conf import settings
from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r"(?P<identifier>.*)\.badge",  views.retrieve_badge),
    url(r'mine/?', views.user_badges),
    url(r'send/?', views.send_badges),
)
