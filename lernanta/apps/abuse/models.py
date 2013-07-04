from django.db import models
from django.conf import settings

from notifications.models import send_notifications_i18n
import logging

log = logging.getLogger(__name__)


def send_abuse_report(url, reason, other, user):
    from users.models import UserProfile
    try:
        profile = UserProfile.objects.get(email=settings.ADMINS[0][1])
        subject_template = 'abuse/emails/abuse_report_subject.txt'
        body_template = 'abuse/emails/abuse_report.txt'
        context = {
            'user': user,
            'url': url,
            'reason': reason,
            'other': other
        }
        send_notifications_i18n([profile], subject_template, body_template,
            context, notification_category='abuse-report'
        )
    except:
        log.debug("Error sending abuse report!")
