from django.utils.http import urlquote
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings

from messages.models import Message
from l10n.urlresolvers import reverse

from users.models import UserProfile
from users.views import get_sso_token


def messages(request):
    if request.user.is_authenticated():
        messages = Message.objects.select_related('sender').filter(
            recipient=request.user,
            recipient_deleted_at__isnull=True)[:3]
        return {'preview_messages': messages}
    else:
        return {}


def redirect_urls(request):
    path = urlquote(request.get_full_path())
    login_url = '%s?%s=%s' % (
        reverse('users_login'), REDIRECT_FIELD_NAME, path)
    register_url = '%s?%s=%s' % (
        reverse('users_register'), REDIRECT_FIELD_NAME, path)
    return {
        'login_with_redirect_url': login_url,
        'register_with_redirect_url': register_url,
    }


def help_sso_token(request):
    if request.user.is_authenticated():
        # if profile was created
        try:
            profile = request.user.get_profile()
        except UserProfile.DoesNotExist:
            return {}
        sso_url = 'http://help.p2pu.org/'
        token = get_sso_token(profile, sso_url)
        return {'help_sso_token': token}
    return {}
