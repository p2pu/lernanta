import time
import urllib2
import logging
import hashlib
import feedparser
import bleach

from django.conf import settings
from django.utils.encoding import smart_str

from celery.schedules import crontab
from celery.decorators import periodic_task

from news.models import FeedEntry

log = logging.getLogger(__name__)


def parse_entry(entry):
    """
    Given a feed entry, return a dictionary with 'title', 'content', 'link',
    'updated'.
    """
    title = getattr(entry, 'title', None)
    if not title:
        log.debug("Feed entry has no title element.")
        return None
    description = getattr(entry, 'description', None)
    content = getattr(entry, 'content', None)
    # some feed entries have a summary but no content
    if not content:
        content = getattr(entry, 'summary', None)
    if  not content:
        log.debug("Feed entry has no content or summary element.")
        return None
    link = getattr(entry, 'link', None)
    if not link:
        log.debug("Feed entry has no link element.")
        return None
    updated = getattr(entry, 'updated_parsed', None)
    if not updated:
        log.debug("Feed entry has no updated element.")
        return None
    if type(content) == type([]):
        content = content[0]
    return {
        'title': title,
        'description': description,
        'content': content,
        'link': link,
        'updated': updated,
    }


def get_feed_entries(feed_url):
    """Grab the 4 most recent feed entries from the splash page feed URL."""
    log.debug('Fetching feed from URL %s' % (feed_url,))
    if not feed_url:
        log.warn('No feed url defined. Cannot update splash page feed.')
        return []
    data = urllib2.urlopen(feed_url).read()
    feed = feedparser.parse(data)
    entries = feed.entries[0:4]
    return entries


def parse_feed(feed_url, page):
    ids = []
    entries = get_feed_entries(feed_url)

    for entry in entries:
        parsed = parse_entry(entry)
        if not parsed:
            log.warn("Parsing feed failed. continuing")
            continue
        if isinstance(parsed['content'], feedparser.FeedParserDict):
            if 'value' in parsed['content'].keys():
                body = parsed['content']['value']
        else:
            body = parsed['content']
        if not body:
            log.warn("Parsing feed failed - no body found")
            continue
        cleaned_body = smart_str(bleach.clean(body, tags=('img',), attributes={'img': ['src', 'alt'], },
                                              strip=True, strip_comments=True))
        try:
            checksum = hashlib.md5(cleaned_body).hexdigest()
            exists = FeedEntry.objects.filter(checksum=checksum)
            if not exists:
                entry = FeedEntry(
                    title=parsed['title'].encode('utf-8'),
                    link=parsed['link'].encode('utf-8'),
                    body=cleaned_body,
                    page=page,
                    checksum=checksum,
                    created_on=time.strftime(
                        "%Y-%m-%d %H:%M:%S", parsed['updated']))
                entry.save()
                ids.append(entry.id)
            else:
                ids.append(exists[0].id)
        except:
            log.warn("Encountered an error creating FeedEntry. Skipping.")
            continue
    return ids


@periodic_task(run_every=crontab(minute=0, hour=0), name='news.tasks.update_feeds')
def update_feeds():
    ids = []
    feeds = getattr(settings, 'FEED_URLS', None)
    if not feeds:
        log.debug("No feeds defined, aborting")
        return
    for page, feed_url in feeds.iteritems():
        parsed = parse_feed(feed_url, page)
        if parsed:
            ids.extend(parsed)
    if ids:
        FeedEntry.objects.exclude(id__in=ids).delete()
