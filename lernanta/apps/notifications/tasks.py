import urllib
import urllib2

from django.conf import settings
from django.contrib.sites.models import Site

from celery.task import Task

from l10n.models import localize_email

class SendNotifications(Task):
    """Send email notification to the users specified by ``profiles``."""
    name = 'notifications.tasks.SendNotifications'

    def run(self, profiles, subject_template, body_template, context, reply_token=None, **kwargs):
        log = self.get_logger(**kwargs)
        subjects, bodies = localize_email(subject_template,
            body_template, context)
            
        from_email = "P2PU Notifications <{0}>".format(settings.DEFAULT_FROM_EMAIL)
        if reply_token:
            from_email = "P2PU Notifications <reply+{0}@{1}>".format(reply_token,
                settings.REPLY_EMAIL_DOMAIN)
            
        for profile in profiles:
            if profile.deleted:
                continue
            subject = subjects[profile.preflang]
            body = bodies[profile.preflang]
            log.debug("Sending email to user %d with subject %s" % (
                profile.user.id, subject,))
            profile.user.email_user(subject, body, from_email)


class PostNotificationResponse(Task):
    """ Send a post to the response URL specified by the token """
    name = 'notifications.tasks.PostNotificationResponse'

    def run(self, token, from_email, text, **kwargs):
        log = self.get_logger(**kwargs)
        log.debug("PostNotificationResponse: invoking callback") 

        data = {
            'from': from_email,
            'text': text,
            'api-key': settings.INTERNAL_API_KEY
        }
        
        host_name = Site.objects.get_current().domain
        url = "https://{0}{1}".format(host_name, token.response_callback)

        try:
            results = urllib2.urlopen(url, urllib.urlencode(data))
        except urllib2.HTTPError as error:
            log.error("calling internal API failed. URL: {0}, Status code: {1}".format(url, error.code))
        except urllib.URLError as error:
            log.error("calling internal API failed. URL: {0}, reason: ".format(url, error.reason))
