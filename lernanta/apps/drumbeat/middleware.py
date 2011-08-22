import re
import urllib
import logging

from django.http import HttpResponseRedirect
from django.conf import settings
from l10n.urlresolvers import reverse
from l10n.locales import LOCALES
from users.models import UserProfile

log = logging.getLogger(__name__)

def look_for_username(path):
    # Generate a pattern like 'de|en|es' to match supported locales.
    recognized_locales = '|'.join(LOCALES.keys())

    # Combine that with a pattern to match a user name.  Note that
    # the locale may or may not be present.
    pattern = '(/(%s))?/([^/]+)/?' % recognized_locales

    # Look for a match in the given path.
    m = re.match(pattern, path)
    if not m:
        return None

    # A match was found, so extract and return the potential user name.
    return m.group(3)

class NotFoundMiddleware(object):

    def process_response(self, request, response):
        if response.status_code == 404:
            # If this URL looks like an old-style user profile URL
            # (i.e., one that does _not_ begin with '/people/...')
            # then redirect to the new-style user profile URL so that
            # people's bookmarks and links won't break.
            username = look_for_username(request.path)
            if username:
                try:
                    user = UserProfile.objects.get(username=username)
                    return HttpResponseRedirect(user.get_absolute_url())
                except UserProfile.DoesNotExist:
                    pass # didn't find a matching user, so fall through to next case

            # Handle old Drupal URLs
            url = settings.DRUPAL_URL + request.path[4:]
            log.error('Not found %s' % url)
            try:
                page = urllib.urlopen(url)
                if page.getcode() != 404:
                    return HttpResponseRedirect(url)
            except UnicodeError:
                pass

        # Not a 404, or we didn't (successfully) handle this request
        # above, so just return whatever response we already have.
        return response
