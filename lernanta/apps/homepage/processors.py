from schools.models import School
from news.models import FeedEntry

from django.core.cache import cache
from django.utils import simplejson as json
from django.utils.encoding import smart_str
from django.conf import settings

import requests
import bleach

import logging
from news.tasks import get_feed_entries
from lernanta.apps.news.tasks import parse_entry

log = logging.getLogger(__name__)


def get_blog_feed():
    feeds = cache.get('blog_feeds')
    if feeds is None:
        feeds_arr = []

        try:
            feeds = get_feed_entries(settings.FEED_URLS['splash'])

            for feed in feeds:
                parsed = parse_entry(feed)
                cleaned_description = smart_str(bleach.clean(parsed['description'], tags=('img',),
                                                             attributes={'img': ['src', 'alt'], }, strip=True,
                                                             strip_comments=True))
                parsed['description'] = cleaned_description
                feeds_arr.append(parsed)
            feeds = feeds_arr
            cache.set('blog_feeds', feeds_arr, 60*60)
        except Exception:
            log.error('Could not fetch list of blog feeds')
    return feeds


def get_featured_badges():
    badges = cache.get('featured_badges')
    if badges is None:
        try:
            badges = requests.get(settings.FEATURED_BADGES_FEED_URL).json
            cache.set('featured_badges', json.dumps(badges), 60*60)
        except Exception:
            log.error('Could not fetch list of featured badges')
    else:
        badges = json.loads(badges)
    return badges
