import requests

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, EmailMultiAlternatives

from celery.task import Task

from l10n.models import localize_email

class TranslateAndSendNotifications(Task):
    """Send email notification to the users specified by ``profiles``."""
    name = 'notifications.tasks.TranslateAndSendNotifications'

    def run(self, profiles, subject_template, body_template, context, sender, **kwargs):
        log = self.get_logger(**kwargs)
        subjects, bodies = localize_email(subject_template,
            body_template, context)

        for profile in profiles:
            if profile.deleted:
                continue
            subject = subjects[profile.preflang]
            body = bodies[profile.preflang]
            log.debug(u"Sending email to %s with subject %s" % (
                profile.user.username, subject,))
            email = EmailMessage(subject, body, sender, [profile.user.email])
            email.send()


class SendNotifications(Task):
    """Send email notification to the users specified by ``profiles``."""
    name = 'notifications.tasks.SendNotifications'

    def run(self, profiles, subject, text_body, html_body=None, sender=None, **kwargs):
        log = self.get_logger(**kwargs)

        for profile in profiles:
            if profile.deleted:
                continue
            log.debug(u"Sending email to %s with subject %s" % (
                profile.user.username, subject,))
            email = EmailMultiAlternatives(subject, text_body, sender, 
                [profile.user.email]
            )
            if html_body:
                email.attach_alternative(html_body, "text/html")
            email.send()


class PostNotificationResponse(Task):
    """ Send a post to the response URL specified by the token """
    name = 'notifications.tasks.PostNotificationResponse'

    def run(self, token, user, text, **kwargs):
        #CS whole token passed in, but only url is used
        #!! internal API key is posted to callback, wont work for external apps!
        #!! should send data as json request?
        log = self.get_logger(**kwargs)
        log.debug("PostNotificationResponse: invoking callback") 

        data = {
            'api-key': settings.INTERNAL_API_KEY,
            'from': user.username,
            'text': text,
        }

        url = token.response_callback
        if token.response_callback.find('http') != 0:
            host_name = Site.objects.get_current().domain
            url = "https://{0}{1}".format(host_name, token.response_callback)

        try:
            results = requests.post(url, data=data)
        except requests.exceptions.RequestException as error:
            log.error("calling internal API failed. URL: {0}, message: ".format(url, error.message))
