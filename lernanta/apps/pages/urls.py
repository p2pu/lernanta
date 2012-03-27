from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('pages.views',
  url(r'^jobs/$', 'jobs_page', name='static_jobs_page'),
  url(r'^staff/$', 'staff_page', name='static_staff_page'),
  url(r'^(?P<slug>[\w\-\. ]+)/$', 'show_page',
      name='static_page_show'),
)
