from django.db import models

from tasks import SendNotifications, PostNotificationResponse

import logging
import random
import string

log = logging.getLogger(__name__)

def _gen_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(32))

class ResponseToken(models.Model):
    """ Store response tokens and callbacks """

    # Unique token used to route response coming in via email
    response_token = models.CharField(max_length=32, blank=False)

    # URL to call when receiving a response
    response_callback = models.CharField(max_length=255, blank=False)

    def save(self):
        """Generate response token."""
        if not self.response_token:
            self.response_token = _gen_token()
            while True:
                existing = ResponseToken.objects.filter(
                    response_token=self.response_token
                ).count()
                if existing == 0:
                    break
                self.response_token = _gen_token()
        super(ResponseToken, self).save()


    def __unicode__(self):
        return self.response_token


def send_notifications(user_profiles, subject_template, body_template,
        template_context, response_callback=None):
    """Asynchronously send email notifications to users
    
    user_profiles - the users to send the notification to
    subject_template - the template to use for the subject
    body_template - the template to use for the body
    template_context - the context to use when rendering the template
    response_callback - url called when a user responds to a notification
        If response_callback is None, it is assumed that the notification
        cannot be responded to
    """
    token_text = None
    if (response_callback):
        token = ResponseToken()
        token.response_callback = response_callback
        token.save()
        token_text = token.response_token
        
    args = (user_profiles, subject_template, body_template, template_context,
        token_text,)

    log.debug("sending notification {0}".format(args))
    SendNotifications.apply_async(args)


def post_notification_response(token, from_email, text):
    args = (token, from_email, text,)
    PostNotificationResponse.apply_async(args)
