import requests
from django.conf import settings

from content2 import models as content_model
from courses import models as course_model


class BadgeNotFoundException(Exception):
    pass


def request_oembedded_content(url):
    """ Retrieves oembed json from API endpoint"""
    endpoint_url = settings.BADGES_OEMBED_URL

    try:
        r = requests.get(endpoint_url, params={'url': url})
    except (requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError) as e:
        return e
    return r


def add_content_from_response(course_uri, url, user_uri):
    content = None
    response = request_oembedded_content(url)
    if response.status_code == 200:
        content = response.json
        content_data = {
            'title': content['title'],
            'content': content['html'],
            'author_uri': user_uri,
        }
        content = content_model.create_content(**content_data)
        course_model.add_course_content(course_uri, content['uri'])
    else:
        raise BadgeNotFoundException
    return content
