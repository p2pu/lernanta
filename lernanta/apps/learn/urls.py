from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^$', 'learn.views.learn',
        name='learn_all'),

    url(r'^schools/(?P<school_slug>[\w-]+)/', 'learn.views.schools',
        name='learn_schools'),

    url(r'^featured/(?P<feature>[\w-]+)/', 'learn.views.featured',
        name='learn_featured'),

    url(r'^tags/$', 'learn.views.learn_tags',
        name='learn_tags'),
)
