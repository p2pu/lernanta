import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from drumbeat.models import ModelBase
from activity.models import Activity, register_filter
from activity.schema import verbs
from preferences.models import AccountPreferences
from notifications.models import send_notifications


log = logging.getLogger(__name__)


class Relationship(ModelBase):
    """
    A relationship between two objects. Source is usually a user but can
    be any ```Model``` instance. Target can also be any ```Model``` instance.
    """
    source = models.ForeignKey(
        'users.UserProfile', related_name='source_relationships')
    target_user = models.ForeignKey(
        'users.UserProfile', null=True, blank=True)
    target_project = models.ForeignKey(
        'projects.Project', null=True, blank=True)

    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('source', 'target_user'),
            ('source', 'target_project'),
        )

    def __unicode__(self):
        return unicode(self.target_user or self.target_project)

    @property
    def object_type(self):
        target = (self.target_user or self.target_project)
        return target.object_type

    def get_absolute_url(self):
        target = (self.target_user or self.target_project)
        return target.get_absolute_url()

    def save(self, *args, **kwargs):
        """Check that the source and the target are not the same user."""
        if (self.source == self.target_user):
            raise ValidationError(
                _('Cannot create self referencing relationship.'))
        super(Relationship, self).save(*args, **kwargs)

    @staticmethod
    def filter_activities(activities):
        ct = ContentType.objects.get_for_model(Relationship)
        return activities.filter(target_content_type=ct)

register_filter('people', Relationship.filter_activities)


###########
# Signals #
###########


def follow_handler(sender, **kwargs):
    rel = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    if not created or not isinstance(rel, Relationship) or rel.deleted:
        return
    activity = Activity(actor=rel.source,
                        verb=verbs['follow'],
                        target_object=rel)
    recipients = []
    if rel.target_user:
        preferences = AccountPreferences.objects.filter(
            user=rel.target_user, key='no_email_new_follower')
        for pref in preferences:
            if pref.value:
                break
        else:
            recipients.append(rel.target_user)
    else:
        activity.scope_object = rel.target_project
        for organizer in rel.target_project.organizers():
            if organizer.user != rel.source:
                preferences = AccountPreferences.objects.filter(
                    user=organizer.user, key='no_email_new_project_follower')
                for pref in preferences:
                    if pref.value:
                        break
                else:
                    recipients.append(organizer.user)
    activity.save()
    subject_template = 'relationships/emails/new_follower_subject.txt'
    body_template = 'relationships/emails/new_follower.txt'
    context = {
        'user': rel.source,
        'project': rel.target_project,
        'domain': Site.objects.get_current().domain
    }
    send_notifications(recipients, subject_template, body_template, context)

post_save.connect(follow_handler, sender=Relationship,
    dispatch_uid='relationships_follow_handler')
