from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^$', 'learn.views.learn',
        name='learn_all'),

    url(r'^schools/(?P<school_slug>[\w-]+)/$', 'learn.views.schools',
        name='learn_schools'),

    url(r'^list/(?P<list_name>[\w-]+)/$', 'learn.views.list',
        name='learn_list'),

    url(r'^fresh/$', 'learn.views.fresh',
        name='learn_fresh'),

    url(r'^tags/$', 'learn.views.learn_tags',
        name='learn_tags'),

    url(r'^auto_complete_lookup/$', 'learn.views.auto_complete_lookup',
        name='learn_auto_complete_lookup'),

    url(r'^add_course/$', 'learn.views.add_course',
        name='learn_add_course'),

    url(r'^api/update_course/$', 'learn.views.update_course',
        name='learn_update_course'),
)
