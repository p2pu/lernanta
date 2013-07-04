from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(r'^abuse/$', 'abuse.views.prompt_abuse_reason',
        name='report_abuse'),

    url(r'^abuse/(?P<model>[\w ]+)/(?P<app_label>[\w ]+)/(?P<pk>\d+)/$',
        'abuse.views.report_abuse',
        name='drumbeat_abuse'),
)
