from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^create/$', 'courses.views.create_course',
        name='courses_create'),

    url(r'^import_project/(?P<project_slug>[\w-]+)/$',
        'courses.views.import_project',
        name='courses_import_project'),

    url(r'^(?P<course_id>[\d]+)/$', 
        'courses.views.course_slug_redirect',
        name='courses_slug_redirect'),

    url(r'^(?P<course_id>[\d]+)/learn_api_data/$', 
        'courses.views.course_learn_api_data',
        name='courses_learn_api_data'),

    url(r'^(?P<course_id>[\d]+)/admin_content/$', 
        'courses.views.course_admin_content',
        name='courses_admin_content'),

    url(r'^(?P<course_id>[\d]+)/discussion/$', 
        'courses.views.course_discussion',
        name='courses_discussion'),

    url(r'^(?P<course_id>[\d]+)/people/$', 
        'courses.views.course_people',
        name='courses_people'),

    url(r'^(?P<course_id>[\d]+)/settings/$', 
        'courses.views.course_settings',
        name='courses_settings'),

    url(r'^(?P<course_id>[\d]+)/signup/$',
        'courses.views.course_signup',
        name='courses_signup'),

    url(r'^(?P<course_id>[\d]+)/upload_image/$',
        'courses.views.course_image',
        name='courses_image'),

    url(r'^(?P<course_id>[\d]+)/add_user/$',
        'courses.views.course_add_user',
        name='courses_add_user'),

    url(r'^(?P<course_id>[\d]+)/change_status/$',
        'courses.views.course_change_status',
        name='courses_change_status'),

    url(r'^(?P<course_id>[\d]+)/change_signup/$',
        'courses.views.course_change_signup',
        name='courses_change_signup'),

    url(r'^(?P<course_id>[\d]+)/change_term/(?P<term>fixed|rolling)/$',
        'courses.views.course_change_term',
        name='courses_change_term'),

    url(r'^(?P<course_id>[\d]+)/update/(?P<attribute>[\w_]+)/$',
        'courses.views.course_update_attribute',
        name='courses_update_attribute'),

    url(r'^(?P<course_id>[\d]+)/update_tags/$',
        'courses.views.course_update_tags',
        name='courses_update_tags'),

    url(r'^(?P<course_id>[\d]+)/update_metadata/$',
        'courses.views.course_update_metadata',
        name='courses_update_metadata'),

    url(r'^(?P<course_id>[\d]+)/(?P<slug>[\w-]+)/$',
        'courses.views.show_course',
        name='courses_show'),

    url(r'^(?P<course_id>[\d]+)/remove_user/(?P<username>[\w\-\. ]+)/$',
        'courses.views.course_leave',
        name='courses_leave'),

    url(r'^(?P<course_id>[\d]+)/add_organizer/(?P<username>[\w\-\. ]+)/$',
        'courses.views.course_add_organizer',
        name='courses_add_organizer'),

    url(r'^(?P<course_id>[\d]+)/content/create/$',
        'courses.views.create_content',
        name='courses_create_content'),

    url(r'content/preview/$',
        'courses.views.preview_content',
        name='courses_preview_content'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/$',
        'courses.views.show_content',
        name='courses_content_show'),
    
    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/edit/$',
        'courses.views.edit_content',
        name='courses_content_edit'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/remove/$',
        'courses.views.remove_content',
        name='courses_content_remove'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/up/$',
        'courses.views.move_content_up',
        name='courses_content_up'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/down/$',
        'courses.views.move_content_down',
        name='courses_content_down'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/comment/$',
        'courses.views.post_content_comment',
        name='courses_post_content_comment'),

    url(r'^(?P<course_id>[\d]+)/content/(?P<content_id>[\d]+)/comment/(?P<comment_id>[\d]+)/reply/$',
        'courses.views.post_comment_reply',
        name='courses_post_comment_reply'),

)
