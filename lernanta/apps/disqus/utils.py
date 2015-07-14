import base64
import hashlib
import hmac
import simplejson
import time
import requests

from django.conf import settings
from django.contrib.sites.models import Site
 
from l10n.urlresolvers import reverse


def get_disqus_sso(user):
    # create a JSON packet of our data attributes
    user_relative_url = reverse(
        'users_profile_view', 
        kwargs={'username': user.username}
    )
    user_url = ''.join([
        'https://',
        Site.objects.get_current().domain,
        user_relative_url
    ])
    data = simplejson.dumps({
        'id': user.username,
        'username': user.username,
        'email': user.email,
        'avatar': user.get_profile().image_or_default(),
        'url': user_url
    })
    # encode the data to base64
    message = base64.b64encode(data)
    # generate a timestamp for signing the message
    timestamp = int(time.time())
    # generate our hmac signature
    sig = hmac.HMAC(settings.DISQUS_SECRET_KEY, '%s %s' % (message, timestamp), hashlib.sha1).hexdigest()
   
    # return a script tag to insert the sso message
    disqus_login_s3 = "%(message)s %(sig)s %(timestamp)s" % dict(
            message=message,
            timestamp=timestamp,
            sig=sig,
    )

    return disqus_login_s3


def get_thread(ident):
    url = 'https://disqus.com/api/3.0/threads/details.json'
    params = {
        'api_key': settings.DISQUS_PUBLIC_KEY,
        'forum': settings.DISQUS_SHORTNAME,
        'thread:ident': ident
    }
    res = requests.get(url, params=params)
    return res.json


def get_thread_posts(ident):
    #TODO this doesn't fetch all the posts!
    url = 'https://disqus.com/api/3.0/threads/listPosts.json'
    params = {
        'api_key': settings.DISQUS_PUBLIC_KEY,
        'forum': settings.DISQUS_SHORTNAME,
        'thread:ident': ident
    }
    res = requests.get(url, params=params)
    return res.json
