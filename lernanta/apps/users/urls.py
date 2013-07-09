from django.conf.urls.defaults import patterns, url
from django.contrib.auth.views import password_reset
from django.views.generic.base import RedirectView

from users.decorators import anonymous_only
from users import forms

urlpatterns = patterns('',

# Login / auth urls
    url(r'^login/$', 'users.views.login',
        name='users_login'),
    url(r'^login/openid/$', 'users.views.login_openid',
        name='users_login_openid'),
    url(r'^login/openid/complete/$', 'users.views.login_openid_complete',
        name='users_login_openid_complete'),
    url(r'^logout/', 'users.views.logout',
        name='users_logout'),

# Reset password urls
    url(r'^forgot/$',
        anonymous_only(password_reset),
        {'template_name': 'users/forgot_password.html',
            'email_template_name': 'users/emails/forgot_password.txt',
            'password_reset_form': forms.PasswordResetForm},
        name='users_forgot_password'),

    url(r'^forgot/sent/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'users/forgot_password_done.html'},
        name='users_forgot_password_done'),

    url(r'^forgot/(?P<uidb36>\w{1,13})/(?P<token>\w{1,13}-\w{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'users/forgot_password_confirm.html',
            'set_password_form': forms.SetPasswordForm},
        name='users_forgot_password_confirm'),

    url(r'^forgot/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'users/forgot_password_complete.html'},
        name='users_forgot_password_complete'),

# Public pages
    url(r'^people/tag/(?P<tag_slug>[\w\-\. ]+)/$',
        'users.views.user_tagged_list', name="users_user_tagged_list"),
    url(r'^people/$', 'users.views.user_list',
        name='users_user_list'),

# Registration urls
    url(r'^register/$', 'users.views.register',
        name='users_register'),
    url(r'^register/openid/$', 'users.views.register_openid',
        name='users_register_openid'),
    url(r'^confirm/resend/$',
        'users.views.confirm_resend',
        name='users_confirm_resend'),
    url(r'^confirm/(?P<token>\w+)/(?P<username>[\w\-\. ]+)/$',
        'users.views.confirm_registration',
        name='users_confirm_registration'),
    url(r'^register/openid/complete/$', 'users.views.register_openid_complete',
        name='users_register_openid_complete'),

# Ajax handlers
    url(r'^ajax/check_username/$', 'users.views.check_username',
        name='users_check_username'),
    url(r'^ajax/following/$', 'users.views.following',
        name='users_followers'),

# Profile urls
    url(r'^(?P<username>[\w\-\. ]+)/$', 'users.views.profile_view',
        name='users_profile_view'),
    url(r'^profile/edit/$', 'users.views.profile_edit',
        name='users_profile_edit'),
    url(r'^profile/edit/badges/$', 'users.views.badges_manage',
        name='users_badges_manage'),
    url(r'^profile/edit/openids/$', 'users.views.profile_edit_openids',
        name='users_profile_edit_openids'),
    url(r'^profile/edit/openids/complete/$',
        'users.views.profile_edit_openids_complete',
        name='users_profile_edit_openids_complete'),
    url(r'^profile/edit/openids/delete/(?P<openid_pk>[\d]+)/$',
        'users.views.profile_edit_openids_delete',
        name='users_profile_edit_openids_delete'),
    url(r'^profile/edit/image/$', 'users.views.profile_edit_image',
        name='users_profile_edit_image'),
    url(r'^profile/edit/ajax_image/$', 'users.views.profile_edit_image_async',
        name='users_profile_edit_image_async'),
    url(r'^profile/link/(?P<counter>\d+)/up/$', 'users.views.link_index_up',
        name='link_index_up'),
    url(r'^profile/link/(?P<counter>\d+)/down/$', 'users.views.link_index_down',
        name='link_index_down'),
    url(r'^profile/edit/links/$', 'users.views.profile_edit_links',
        name='users_profile_edit_links'),
    url(r'^profile/edit/links/edit/(?P<link_id>[\d]+)/$',
        'users.views.profile_edit_links_edit',
        name='users_profile_edit_links_edit'),
    url(r'^profile/edit/links/delete/(?P<link>[\d]+)/$',
        'users.views.profile_edit_links_delete',
        name='users_profile_edit_links_delete'),
    url(r'^profile/edit/settings/$', 
        RedirectView.as_view(url='/profile/edit/notifications/')),
    url(r'^profile/edit/notifications/$', 'preferences.views.notifications',
        name='preferences_notifications'),
    url(r'^profile/edit/email/$', 'preferences.views.email',
        name='preferences_email'),
    url(r'^profile/edit/password/$', 'preferences.views.password',
        name='preferences_password'),
    url(r'^profile/delete/$', 'preferences.views.delete',
        name='preferences_delete'),
    url(r'^profile/create/$', 'users.views.profile_create',
        name='users_profile_create'),
)
