import logging
import datetime

from django.db import models
from django.contrib.sites.models import Site

from drumbeat.models import ModelBase
from richtext.models import RichTextField
from notifications.models import send_notifications_i18n

log = logging.getLogger(__name__)


class Reviewer(ModelBase):
    user = models.ForeignKey('users.UserProfile')
    can_delete = models.BooleanField()
    can_feature = models.BooleanField()

    def __unicode__(self):
        return unicode(self.user)


class Review(ModelBase):

    project = models.ForeignKey('projects.Project', related_name='reviews')
    author = models.ForeignKey('users.UserProfile', related_name='reviews')
    accepted = models.BooleanField(default=False)
    mark_deleted = models.BooleanField(default=False)
    mark_featured = models.BooleanField(default=False)
    content = RichTextField(config_name='rich', blank=False)
    created_on = models.DateTimeField(auto_now_add=True,
        default=datetime.datetime.now)

    def __unicode__(self):
        return 'Review for %s' % self.project.name

    @models.permalink
    def get_absolute_url(self):
        return ('show_project_reviews', (), {
            'slug': self.project.slug,
        })

    def send_notifications_i18n(self):
        subject_template = 'reviews/emails/review_submitted_subject.txt'
        body_template = 'reviews/emails/review_submitted.txt'
        context = {
            'course': self.project.name,
            'reviewer': self.author.username,
            'review_text': self.content,
            'review_url': self.get_absolute_url(),
            'domain': Site.objects.get_current().domain, 
        }
        profiles = [recipient.user for recipient in self.project.organizers()]
        send_notifications_i18n(profiles, subject_template, body_template,
            context,
            notification_category=u'course-review.project-{0}'.format(self.project.slug)
        )
