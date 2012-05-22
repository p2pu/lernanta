from django.conf.urls.defaults import patterns, url
from django.views.generic import RedirectView


urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='inbox/')),
    url(r'^inbox/$', 'drumbeatmail.views.inbox',
        name='drumbeatmail_inbox'),
    url(r'^inbox/(?P<page_number>[\d]+)/$', 'drumbeatmail.views.inbox',
        name='drumbeatmail_inbox_offset'),
    url(r'^inbox/(?P<filter>[\w\-\. ]+)/$',
        'drumbeatmail.views.inbox_filtered',
        name='drumbeatmail_inbox_filtered'),
    url(r'^inbox/(?P<filter>[\w\-\. ]+)/(?P<page_number>[\d]+)/$',
        'drumbeatmail.views.inbox_filtered',
        name='drumbeatmail_inbox_filtered_offset'),
    url(r'^outbox/$', 'drumbeatmail.views.outbox',
        name='drumbeatmail_outbox'),
    url(r'^outbox/(?P<page_number>[\d]+)/$', 'drumbeatmail.views.outbox',
        name='drumbeatmail_outbox_offset'),
    url(r'^compose/$', 'drumbeatmail.views.compose',
        name='drumbeatmail_compose'),
    url(r'^(?P<username>[\w\-\. ]+)/$', 'drumbeatmail.views.compose',
        name='drumbeatmail_compose_to'),
    url(r'^reply/(?P<message>[\d]+)/$', 'drumbeatmail.views.reply',
        name='drumbeatmail_reply'),
)
