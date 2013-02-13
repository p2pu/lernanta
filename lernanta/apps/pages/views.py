from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import get_language
from django import http

from pages.models import Page


import logging
log = logging.getLogger(__name__)


def show_page(request, slug):
    """ Shows the page identified with slug translated to the current language
    or in its original language if there is not translation.
    """
    curlang = get_language()
    try:
        page = Page.objects.get(slug=slug, language=curlang)
    except Page.DoesNotExist:
        page = get_object_or_404(Page, slug=slug, language='en')
    return render_to_response(
        'pages/page.html', {'page': page, },
        context_instance=RequestContext(request)
    )
