import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.utils.translation import get_language

from pages.models import Page


import logging
log = logging.getLogger(__name__)


def show_page(request, slug):
    """ Shows the page identified with slug translated to the current language
    or in its original language if there is not translation.
    """
    curlang = get_language()
    page = get_object_or_404(Page, slug=slug)
    if page.language != curlang:
        if page.original != None:
            page = get_object_or_404(Page, pk=page.original.id)
        assert(page.original == None)
        if page.language != curlang:
            translations = Page.objects.filter(original = page.id)
            for tpage in translations:
                if tpage.language == curlang:
                    page = tpage
                    break
    return render_to_response(
        'pages/page.html', {'page': page, }, 
        context_instance=RequestContext(request)
    )

