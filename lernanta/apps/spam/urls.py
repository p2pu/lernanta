from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^delete_spammer/(?P<username>[\w\-\. ]+)/$',
        'spam.views.delete_spammer',
        name='spam_delete_spammer'
    ),
)
