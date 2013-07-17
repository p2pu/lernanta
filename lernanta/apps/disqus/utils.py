import base64
import hashlib
import hmac
import simplejson
import time

from django.conf import settings
 
def get_disqus_sso(user):
    # create a JSON packet of our data attributes
    data = simplejson.dumps({
      'id': user.username,
      'username': user.username,
      'email': user.email,
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
