from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'homepage.views.home', name='home'),
)
