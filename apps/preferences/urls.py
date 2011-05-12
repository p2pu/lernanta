from django.conf.urls.defaults import patterns, url

from preferences import forms

urlpatterns = patterns('',
  url(r'^settings/', 'preferences.views.settings',
      name='preferences_settings'),
  url(r'^email/', 'preferences.views.email',
      name='preferences_email'),
  url(r'^password/', 'preferences.views.password',
      name='preferences_password'),
  url(r'^delete/', 'preferences.views.delete',
      name='preferences_delete'),

)
