from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate, get_language, ugettext

from l10n.urlresolvers import reverse
from messages.models import Message
from users.tasks import SendUserEmail
from preferences.models import AccountPreferences

import logging

log = logging.getLogger(__name__)


def message_sent_handler(sender, **kwargs):
    message = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    if not created or not isinstance(message, Message):
        return
    user = message.recipient
    preferences = AccountPreferences.objects.filter(
        user=user.get_profile())
    for preference in preferences:
        if preference.value and preference.key == 'no_email_message_received':
            return
    sender = message.sender.get_profile().display_name
    ulang = get_language()
    activate(user.get_profile().preflang or settings.LANGUAGE_CODE)
    subject = ugettext('New Message from %(display_name)s' % {
        'display_name': sender,
        })
    body = render_to_string('drumbeatmail/emails/direct_message.txt', {
        'sender': sender,
        'message': message.body,
        'domain': Site.objects.get_current().domain,
        'reply_url': reverse('drumbeatmail_reply', kwargs={
            'message': message.pk,
            }),
        })
    activate(ulang)
    SendUserEmail.apply_async((user.get_profile(), subject, body))
post_save.connect(message_sent_handler, sender=Message)
