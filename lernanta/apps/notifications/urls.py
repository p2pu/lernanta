from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^response/$', 'notifications.views.response',
        name='notifications_response'),
    url(r'^notification/$', 'notifications.views.notifications_create',
        name='notifications_create'),
)
