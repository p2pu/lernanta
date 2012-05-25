from django.conf.urls.defaults import patterns, url, include


urlpatterns = patterns('',
    (r'^obi/', include('django_obi.urls')),
    url(r'^submissions/$',
        'badges.views.submissions_list',
        name="submissions_list"),

    url(r'^submissions/awarded/$',
        'badges.views.awarded_submissions_list',
        name="awarded_submissions_list"),

    url(r'^submissions/mine/$',
        'badges.views.mine_submissions_list',
        name="mine_submissions_list"),

    url(r'^$', 'badges.views.badges_list',
        name='badges_list'),

    url(r'^create/$', 'badges.views.create_badge',
        name='badges_create'),

    url(r'^(?P<slug>[\w-]+)/$', 'badges.views.show_badge',
        name='badges_show'),

    url(r'^(?P<slug>[\w-]+)/submissions/create/$',
        'badges.views.create_submission',
        name='submission_create'),

    url(r'^(?P<slug>[\w-]+)/submissions/$',
        'badges.views.matching_submissions',
        name='matching_submissions'),

    url(r'^(?P<slug>[\w-]+)/submissions/awarded/$',
        'badges.views.awarded_matching_submissions',
        name='awarded_matching_submissions'),

    url(r'^(?P<slug>[\w-]+)/submissions/mine/$',
        'badges.views.mine_matching_submissions',
        name='mine_matching_submissions'),

    url(r'^(?P<slug>[\w-]+)/submissions/(?P<submission_id>\d+)/$',
        'badges.views.show_submission',
        name='submission_show'),

    url(r'^(?P<slug>[\w-]+)/submissions/(?P<submission_id>\d+)/assess/$',
        'badges.views.assess_submission',
        name='assess_submission'),

    url(r'(?P<slug>[\w-]+)/assessments/create/$',
        'badges.views.create_assessment',
        name='assessment_create'),

    url(r'^(?P<slug>[\w-]+)/matching_peers/$',
        'badges.views.matching_peers',
        name='matching_peers'),

    url(r'(?P<slug>[\w-]+)/assessments/(?P<assessment_id>\d+)/$',
        'badges.views.show_assessment',
        name='assessment_show'),

    url(r'(?P<slug>[\w-]+)/awards/(?P<username>[\w\-\. ]+)/$',
        'badges.views.show_user_awards',
        name='user_awards_show'),

    url(r'(?P<slug>[\w-]+)/other_badges/$',
        'badges.views.other_badges',
        name='other_badges'),
)
