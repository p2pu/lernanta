from django.conf.urls.defaults import patterns, url
from django.views.generic.base import TemplateView

urlpatterns = patterns('pages.views',
    url(r'^get-involved/$',
        TemplateView.as_view(template_name='pages/get_involved_page.html'),
        name='static_get_involved_page'),
    url(r'^(?P<slug>[\w\-\. ]+)/$', 'show_page', name='static_page_show'),
)
