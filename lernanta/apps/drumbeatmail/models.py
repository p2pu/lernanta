from django.db.models.signals import post_save
from django.contrib.sites.models import Site

from l10n.urlresolvers import reverse
from messages.models import Message
from notifications.models import send_notifications_i18n
from richtext import clean_html

import logging

log = logging.getLogger(__name__)


def message_sent_handler(sender, **kwargs):
    message = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    if not created or not isinstance(message, Message):
        return
    recipient = message.recipient.get_profile()
    sender = message.sender.get_profile()
    reply_url = reverse('drumbeatmail_reply', kwargs={'message': message.pk})
    msg_body = clean_html('rich', message.body)
    subject_template = 'drumbeatmail/emails/direct_message_subject.txt'
    body_template = 'drumbeatmail/emails/direct_message.txt'
    context = {
        'sender': sender,
        'message': msg_body,
        'domain': Site.objects.get_current().domain,
        'reply_url': reply_url,
    }
    send_notifications_i18n([recipient], subject_template, body_template, context,
        notification_category='direct-message'
    )

post_save.connect(message_sent_handler, sender=Message,
    dispatch_uid='drumbeatmail_message_sent_handler')
