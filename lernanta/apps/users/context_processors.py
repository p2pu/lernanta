from django.utils.http import urlquote
from django.contrib.auth import REDIRECT_FIELD_NAME

from messages.models import Message
from l10n.urlresolvers import reverse


def messages(request):
    if request.user.is_authenticated():
        messages = Message.objects.select_related('sender').filter(
            recipient=request.user,
            recipient_deleted_at__isnull=True)[:3]
        return {'preview_messages': messages}
    else:
        return {}


def redirect_urls(request):
    login_url = reverse('users_login')
    register_url = reverse('users_register')
    return {
        'login_with_redirect_url': login_url,
        'register_with_redirect_url': register_url,
    }
