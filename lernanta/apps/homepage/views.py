import random

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.gzip import gzip_page

from learn.models import get_courses_by_list

from processors import get_blog_feed
from processors import get_featured_badges


def _pick_n(sequence, n):
    if sequence:
        sequence = random.sample(sequence, min(n,len(sequence)))
    return sequence


@gzip_page
def home(request):
    feed_entries = get_blog_feed()
    courses = _pick_n(get_courses_by_list("showcase"), 3)
    badges = _pick_n(get_featured_badges(), 3)

    return render_to_response('homepage/home.html', {
        'feed_entries':  feed_entries,
        'courses': courses,
        'badges': badges,
    }, context_instance=RequestContext(request))
