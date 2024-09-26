import random

from django import http
from django.shortcuts import render_to_response
from django.template import RequestContext

from l10n.urlresolvers import reverse

from learn.models import get_courses_by_list

from processors import get_blog_feed
from processors import get_featured_badges


def _pick_n(sequence, n):
    if sequence:
        sequence = random.sample(sequence, min(n, len(sequence)))
    return sequence


def home(request):
    learn_url = reverse('learn_list', kwargs={'list_name':'community'})
    return http.HttpResponseRedirect(learn_url)
