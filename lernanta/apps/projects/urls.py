from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^create/$', 'projects.views.create',
        name='projects_create'),

    url(r'^(?P<slug>[\w-]+)/create/overview/$', 'projects.views.create_overview',
        name='projects_create_overview'),

    url(r'^(?P<slug>[\w-]+)/create/tasks/$', 'projects.views.create_tasks',
        name='projects_create_tasks'),

    url(r'^(?P<slug>[\w-]+)/create/review/$', 'projects.views.create_review',
        name='projects_create_review'),

    url(r'^create/matching_kinds/$',
        'projects.views.matching_kinds',
        name='matching_kinds'),

    url(r'^clone/$', 'projects.views.clone',
        name='projects_clone'),

    url(r'^clone/matching_projects/$',
        'projects.views.matching_projects',
        name='matching_projects'),

    url(r'^import/$', 'projects.views.import_from_old_site',
        name='projects_import'),

    url(r'^import/matching_courses/$',
        'projects.views.matching_courses',
        name='matching_courses'),

    url(r'^(?P<slug>[\w-]+)/$', 'projects.views.show',
        name='projects_show'),

    url(r'^(?P<slug>[\w-]+)/people/$', 'projects.views.user_list',
        name='projects_user_list'),

    url(r'^(?P<slug>[\w-]+)/contact_organizers/$',
        'projects.views.contact_organizers',
        name='projects_contact_organizers'),

    url(r'^(?P<slug>[\w-]+)/tasks/$', 'projects.views.task_list',
        name='projects_task_list'),

    url(r'^(?P<slug>[\w-]+)/discussions/$', 'projects.views.discussion_area',
        name='projects_discussion_area'),

    # Project Content URLs
    (r'^(?P<slug>[\w-]+)/links/', include('links.urls')),
    
    (r'^(?P<slug>[\w-]+)/sign-up/', include('signups.urls')),
    
    url(r'^(?P<slug>[\w-]+)/content/' +
        '(?P<page_slug>[\w-]+)/toggle_task_completion/$',
        'projects.views.toggle_task_completion',
        name='toggle_task_completion'),

    (r'^(?P<slug>[\w-]+)/content/', include('content.urls')),


    # Project Edit URLs
    url(r'^(?P<slug>[\w-]+)/edit/$', 'projects.views.edit',
        name='projects_edit'),

    url(r'^(?P<slug>[\w-]+)/edit/image/$',
        'projects.views.edit_image',
        name='projects_edit_image'),

    url(r'^(?P<slug>[\w-]+)/edit/ajax_image/$',
        'projects.views.edit_image_async',
        name='projects_edit_image_async'),

    url(r'^(?P<slug>[\w-]+)/edit/links/$',
        'projects.views.edit_links',
        name='projects_edit_links'),

    url(r'^(?P<slug>[\w-]+)/edit/links/(?P<link>\d+)/edit/$',
        'projects.views.edit_links_edit',
        name='projects_edit_links_edit'),

    url(r'^(?P<slug>[\w-]+)/edit/links/(?P<link>\d+)/delete/$',
        'projects.views.edit_links_delete',
        name='projects_edit_links_delete'),

    url(r'^(?P<slug>[\w-]+)/edit/participants/$',
        'projects.views.edit_participants',
        name='projects_edit_participants'),

    url(r'^(?P<slug>[\w-]+)/edit/participants/(?P<username>[\w\-\. ]+)/delete/$',
        'projects.views.edit_participants_delete',
        name='projects_edit_participants_delete'),

    url(r'^(?P<slug>[\w-]+)/edit/participants/' +
        '(?P<username>[\w\-\. ]+)/make_organizer/$',
        'projects.views.edit_participants_make_organizer',
        name='projects_edit_participants_make_organizer'),
        
    url(r'^(?P<slug>[\w-]+)/edit/participants/' +
        '(?P<username>[\w\-\. ]+)/organizer_delete/$',
        'projects.views.edit_participants_organizer_delete',
        name='projects_edit_participants_organizer_delete'),

    url(r'^(?P<slug>[\w-]+)/edit/participants/matching_non_participants/$',
        'projects.views.matching_non_participants',
        name='matching_non_participants'),

    url(r'^(?P<slug>[\w-]+)/edit/next_steps/$',
        'projects.views.edit_next_steps',
        name='projects_edit_next_steps'),

    url(r'^(?P<slug>[\w-]+)/edit/next_steps/(?P<step_slug>[\w-]+)/delete/$',
        'projects.views.edit_next_steps_delete',
        name='projects_edit_next_steps_delete'),

    url(r'^(?P<slug>[\w-]+)/edit/next_steps/matching_non_next_steps/$',
        'projects.views.matching_non_next_steps',
        name='matching_non_next_steps'),

    url(r'^(?P<slug>[\w-]+)/edit/status/$',
        'projects.views.edit_status',
        name='projects_edit_status'),

    url(r'^(?P<slug>[\w-]+)/admin/metrics/$',
        'projects.views.admin_metrics',
        name='projects_admin_metrics'),

    url(r'^(?P<slug>[\w-]+)/admin/metrics_data',
        'projects.views.admin_metrics_data_ajax',
        name='projects_admin_metrics_data'),

    url(r'^(?P<slug>[\w-]+)/admin/export_detailed_csv/$',
        'projects.views.export_detailed_csv',
        name='projects_admin_export_detailed_csv'),

    url(r'(?P<slug>[\w-]+)/edit/publish/$',
        'projects.views.publish',
        name='projects_publish'),
)
