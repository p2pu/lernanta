import simplejson as json

from content2 import db
from drumbeat.utils import slugify
from django.utils.translation import ugettext as _

import logging
log = logging.getLogger(__name__)


def content_uri2id(content_uri):
    return content_uri.strip('/').split('/')[-1]


def get_content(content_uri, fields=[]):
    content_id = content_uri2id(content_uri)
    try:
        wrapper_db = db.Content.objects.get(id=content_id)
        latest_db = wrapper_db.latest
    except Exception, e:
        #TODO
        log.debug(e)
        return None
    
    content = {
        "id": wrapper_db.id,
        "uri": "/uri/content/{0}".format(wrapper_db.id),
        "title": latest_db.title,
        "content": latest_db.content,
    }
    if "history" in fields:
        content["history"] = []
        for version in wrapper_db.versions.sort_by("date"):
            content['history'] += {
                "date": version.date,
                "author_uri": version.author_uri,
                "title": version.title,
                "comment": version.comment,
            }

    return content


def create_content(title, content, author_uri):
    #TODO check all required properties
    container_db = db.Content()
    container_db.save()
    content_db = db.ContentVersion(
        container=container_db,
        title=title,
        content=content,
        author_uri = author_uri,
    )
    #TODO if "comment" in content:
    #    content_db.comment = content["comment"]
    content_db.save()
    container_db.latest = content_db
    container_db.save()
    return get_content("/uri/content/{0}".format(container_db.id))


def update_content( uri, title, content, author_uri ):
    content_id = content_uri2id(uri)
    try:
        wrapper_db = db.Content.objects.get(id=content_id)
    except Exception, e:
        #TODO
        log.debug(e)
        return None

    content_db = db.ContentVersion(
        container=wrapper_db,
        title=title,
        content=content,
        author_uri = author_uri,
    )
    #TODO if "comment" in content:
    #    content_db.comment = content["comment"]
    content_db.save()
    wrapper_db.latest = content_db
    wrapper_db.save()
    return get_content("/uri/content/{0}".format(wrapper_db.id))


def clone_content(uri):
    content_id = content_uri2id(uri)
    try:
        original_db = db.Content.objects.get(id=content_id)
    except Exception, e:
        log.debug(e)
        raise

    container_db = db.Content(based_on=original_db)
    container_db.save()

    content_db = db.ContentVersion(
        container=container_db,
        title=original_db.latest.title,
        content=original_db.latest.content,
        author_uri=original_db.latest.author_uri,
    )
    content_db.save()
    container_db.latest = content_db
    container_db.save()

    return get_content("/uri/content/{0}".format(container_db.id))
