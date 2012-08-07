import datetime

from django.db import models
from django.db.models.signals import post_save
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from activity.models import Activity, register_filter
from activity.schema import object_types, verbs
from drumbeat.models import ModelBase
from notifications.models import send_notifications
from richtext.models import RichTextField
from l10n.urlresolvers import reverse


class Status(ModelBase):
    object_type = object_types['status']

    author = models.ForeignKey('users.UserProfile')
    project = models.ForeignKey('projects.Project', null=True, blank=True)
    status = RichTextField(blank=False)
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    important = models.BooleanField(default=False)

    activity = generic.GenericRelation(Activity,
        content_type_field='target_content_type',
        object_id_field='target_id')

    class Meta:
        verbose_name_plural = _('statuses')

    def __unicode__(self):
        return _('message: %s') % self.status

    def get_absolute_url(self):
        ct = ContentType.objects.get_for_model(Status)
        activity = Activity.objects.get(target_id=self.id,
            target_content_type=ct)
        return activity.get_absolute_url()

    def send_wall_notification(self):
        if not self.project:
            return
        recipients = self.project.participants()
        subject_template = 'statuses/emails/wall_updated_subject.txt'
        body_template = 'statuses/emails/wall_updated.txt'
        context = {
            'status': self,
            'project': self.project,
            'domain': Site.objects.get_current().domain,
        }
        from_organizer = self.project.organizers().filter(
            user=self.author).exists()
        profiles = []
        for recipient in recipients:
            profile = recipient.user
            if self.important:
                unsubscribed = False
            elif from_organizer:
                unsubscribed = recipient.no_organizers_wall_updates
            else:
                unsubscribed = recipient.no_participants_wall_updates
            if self.author != profile and not unsubscribed:
                profiles.append(profile)

        kwargs = {
            'page_app_label':'activity',
            'page_model': 'activity',
            'page_pk' : self.activity.get().id,
        }
        if self.project:
            kwargs.update({
                'scope_app_label': 'projects',
                'scope_model': 'project',
                'scope_pk': self.project.id,
            })
        callback_url = reverse('page_comment_callback', kwargs=kwargs)
    
        send_notifications( profiles, subject_template, body_template, context,
            callback_url, self.author.username )

    @staticmethod
    def filter_activities(activities):
        ct = ContentType.objects.get_for_model(Status)
        return activities.filter(target_content_type=ct)

register_filter('messages', Status.filter_activities)


###########
# Signals #
###########


def status_creation_handler(sender, **kwargs):
    status = kwargs.get('instance', None)
    created = kwargs.get('created', False)

    if not created or not isinstance(status, Status):
        return

    # fire activity
    activity = Activity(
        actor=status.author,
        verb=verbs['post'],
        target_object=status,
    )
    if status.project:
        activity.scope_object = status.project
    activity.save()
    # Send notifications.
    if status.project:
        status.send_wall_notification()

post_save.connect(status_creation_handler, sender=Status,
    dispatch_uid='statuses_status_creation_handler')
