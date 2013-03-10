from django.conf import settings

from tasks import TranslateAndSendNotifications
from tasks import PostNotificationResponse
from tasks import SendNotifications
from tracker import statsd
from notifications.db import ResponseToken

import datetime
import logging

log = logging.getLogger(__name__)


def _prepare_from_address(sender=None, token=None):
    from_name = "P2PU Notifications"
    if sender:
        from_name = sender

    from_email = "{0} <{1}>".format(from_name, settings.DEFAULT_FROM_EMAIL)
    if token:
        from_email = "{0} <reply+{1}@{2}>".format(from_name, token.response_token,
            settings.REPLY_EMAIL_DOMAIN)

    return from_email


def send_notifications_i18n(user_profiles, subject_template, body_template,
        template_context, response_callback=None, sender=None):
    """Asynchronously send internationalized email notifications to users
    
    user_profiles - the users to send the notification to
    subject_template - the template to use for the subject
    body_template - the template to use for the body
    template_context - the context to use when rendering the template
    response_callback - url called when a user responds to a notification
        If response_callback is None, it is assumed that the notification
        cannot be responded to
    sender - the name to be used in the from address: sender <reply+token@domain>
    """
    token = None
    if (response_callback):
        token = ResponseToken(response_callback=response_callback)
        token.save()
        
    from_email = _prepare_from_address(sender, token)

    args = (user_profiles, subject_template, body_template, template_context,
        from_email)

    log.debug("notifications.send_notifications_i18n: {0}".format(args))
    TranslateAndSendNotifications.apply_async(args)


def send_notifications(user_profiles, subject, text_body, html_body=None,
        response_callback=None, sender=None):
    """Asynchronously send email notifications to users
    html_body - optional html body for the notification
    response_callback - url called when a user responds to a notification
        If response_callback is None, it is assumed that the notification
        cannot be responded to
    sender - the name to be used in the from address: sender <reply+token@domain>
    """

    token = None
    if (response_callback):
        token = ResponseToken(response_callback=response_callback)
        token.save()
  
    from_email = _prepare_from_address(sender, token)      
    args = (user_profiles, subject, text_body, html_body, from_email)

    log.debug(u"notifications.send_notifications: {0}".format(args))
    SendNotifications.apply_async(args)


def _auto_response_filter(token, text):
    """ check if we think this is a auto response """
    delta = datetime.datetime.now() - token.creation_date
    total_seconds = delta.seconds + delta.days * 24 * 3600 # hello python 2.6
    if total_seconds < settings.MIN_EMAIL_RESPONSE_TIME:
        return True

    for trigger_word in settings.AUTO_REPLY_KEYWORDS:
        if trigger_word in text:
            return True

    return False


def post_notification_response(token, user, text):
    """ create response task and run asynchronously """

    if _auto_response_filter(token, text):
        subject_template = 'notifications/emails/response_bounce_subject.txt'
        body_template = 'notifications/emails/response_bounce.txt'
        context = { 'original_message': text }
        send_notifications_i18n([user], subject_template, body_template, context)
        log.debug('post_notification_response: quick response bounced')
        statsd.Statsd.increment('auto-replies')
        return

    args = (token, user, text,)
    PostNotificationResponse.apply_async(args)
