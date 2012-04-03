from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('pages.views',
  url(r'^get-involved/$', 'get_involved_page',
    name='static_get_involved_page'),
  url(r'^jobs/$', 'jobs_page', name='static_jobs_page'),
  url(r'^(?P<slug>[\w\-\. ]+)/$', 'show_page', name='static_page_show'),
)
