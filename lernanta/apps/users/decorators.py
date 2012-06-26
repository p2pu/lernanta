import urllib2

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

from drumbeat import messages
from users.models import UserProfile
from l10n.urlresolvers import reverse


def anonymous_only(func):
    """
    Opposite of ``django.contrib.auth.decorators.login_required``. This
    decorator is for views that redirect users to the redirect field name
    if they are already logged in.
    """

    def decorator(*args, **kwargs):
        request = args[0]
        if request.user.is_authenticated():
            messages.info(request,
                          _("You are already logged into an account."))
            return HttpResponseRedirect(reverse('dashboard'))
        return func(*args, **kwargs)
    return decorator


def login_required(func=None, profile_required=True):
    """
    Custom implementation of ``django.contrib.auth.decorators.login_required``.
    This version has an optional parameter, ``profile_required`` which, if
    True, will check that a user is both authenticated and has a profile. This
    is useful so that the create profile page can load successfully, but a user
    will still be locked out of other views.
    """
    if profile_required:
        test = lambda u: (u.is_authenticated() and
                          UserProfile.objects.filter(user=u).count() > 0)
    else:
        test = lambda u: u.is_authenticated()
    actual_decorator = user_passes_test(test)
    if func:
        return actual_decorator(func)
    return actual_decorator


def secure_required(func):
    """
    This decorator is for views that require https.

    Enabled only if settings.SESSION_COOKIE_SECURE is set to True.
    """
    def decorator(*args, **kwargs):
        request = args[0]
        enabled_https = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        if enabled_https and not request.is_secure():
            http_url = request.build_absolute_uri(request.get_full_path())
            https_url = 'https:' + urllib2.splittype(http_url)[1]
            return HttpResponseRedirect(https_url)
        return func(*args, **kwargs)
    return decorator
