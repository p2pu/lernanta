from django.db import models
from django.conf import settings

import caching.base

from notifications.models import send_notifications
import logging

log = logging.getLogger(__name__)


class ManagerBase(caching.base.CachingManager, models.Manager):
    pass


class ModelBase(caching.base.CachingMixin, models.Model):
    objects = caching.base.CachingManager()

    class Meta:
        abstract = True


def send_abuse_report(url, reason, other, user):
    from users.models import UserProfile
    try:
        profile = UserProfile.objects.get(email=settings.ADMINS[0][1])
        subject_template = 'drumbeat/emails/abuse_report_subject.txt'
        body_template = 'drumbeat/emails/abuse_report.txt'
        context = {
            'user': user,
            'url': url,
            'reason': reason,
            'other': other
        }
        send_notifications([profile], subject_template, body_template, context)
    except:
        log.debug("Error sending abuse report!")
