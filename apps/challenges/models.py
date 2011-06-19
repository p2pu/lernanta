from datetime import datetime
import logging
import bleach

from markdown import markdown

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from drumbeat import storage
from drumbeat.utils import get_partition_id, safe_filename
from drumbeat.models import ModelBase

from projects.models import Project
from statuses.models import Status
from users.tasks import SendUserEmail

import caching.base

TAGS = ('h1', 'h2', 'a', 'b', 'em', 'i', 'strong',
        'ol', 'ul', 'li', 'hr', 'blockquote', 'p',
        'span', 'pre', 'code', 'img')

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt'],
}

log = logging.getLogger(__name__)


def determine_image_upload_path(instance, filename):
    return "images/challenges/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk),
        'filename': safe_filename(filename),
    }


class ChallengeManager(caching.base.CachingManager):
    def active(self, project_id=0):
        q = Challenge.objects.filter(
            start_date__lte=datetime.now()).filter(
            end_date__gte=datetime.now())
        if project_id:
            q = q.filter(project__id=project_id)
        return q

    def upcoming(self, project_id=0):
        q = Challenge.objects.filter(
            end_date__gte=datetime.now())
        if project_id:
            q = q.filter(project__id=project_id)
        return q


class Challenge(ModelBase):
    """ Inovation (design) Challenges """
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    title_long = models.CharField(max_length=255)
    brief = models.TextField()
    guidelines = models.TextField()
    important_dates = models.TextField()
    resources = models.TextField()
    rules = models.TextField()

    sidebar = models.TextField(null=True, blank=True)
    above_fold = models.TextField(null=True, blank=True)

    start_date = models.DateTimeField(default=datetime.now())
    end_date = models.DateTimeField()

    image = models.ImageField(upload_to=determine_image_upload_path, null=True,
                              storage=storage.ImageStorage(), blank=True)

    project = models.ForeignKey(Project)
    created_by = models.ForeignKey('users.UserProfile',
                                   related_name='challenges')
    created_on = models.DateTimeField(auto_now_add=True,
                                      default=datetime.now())

    is_open = models.BooleanField()
    allow_voting = models.BooleanField(default=False)
    entrants_can_edit = models.BooleanField(default=True)

    objects = ChallengeManager()

    def is_active(self):
        return (self.start_date < datetime.now() and
                self.end_date > datetime.now())

    @models.permalink
    def get_absolute_url(self):
        return ('challenges_show', (), {
            'slug': self.slug,
        })

    def __unicode__(self):
        return u"%s (%s - %s)" % (
            self.title,
            datetime.strftime(self.start_date, "%b %d %Y"),
            datetime.strftime(self.end_date, "%b %d %Y"))

    def save(self):
        """Make sure each challenge has a unique slug."""
        count = 1
        if not self.slug:
            slug = slugify(self.title)
            self.slug = slug
            while True:
                existing = Challenge.objects.filter(slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = slug + str(count)
                count += 1
        super(Challenge, self).save()


class Submission(ModelBase):
    """ A submitted entry for a Challenge."""
    title = models.CharField(max_length=100)
    summary = models.TextField()
    description = models.TextField(null=True, blank=True)
    description_html = models.TextField(null=True, blank=True)

    keywords = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    challenge = models.ManyToManyField(Challenge)
    created_by = models.ForeignKey('users.UserProfile',
                                   related_name='submissions')
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.now())

    is_published = models.BooleanField(default=True)

    def get_challenge(self):
        challenges = self.challenge.all()
        if challenges:
            return challenges[0]
        else:
            return None

    def publish(self):
        self.is_published = True
        self.save()

        challenge = self.get_challenge()

        # Create activity
        msg = '<a href="%s">%s</a>: %s | <a href="%s">Read more</a>' % (
            challenge.get_absolute_url(), challenge.title, self.title,
            self.get_absolute_url())
        status = Status(author=self.created_by,
                        project=challenge.project,
                        status=msg)
        status.save()

        # Send thanks email
        user = self.created_by
        share_url = reverse('submission_edit_share', kwargs={
            'slug': challenge.slug,
            'submission_id': self.pk
        })
        submission_url = reverse('submission_show', kwargs={
            'slug': challenge.slug,
            'submission_id': self.pk
        })
        subj = _('Thanks for entering in the Knight-Mozilla Innovation Challenge!')
        body = render_to_string('challenges/emails/submission_thanks.txt', {
            'share_url': share_url,
            'submission_url': submission_url,
        })

        SendUserEmail.apply_async((user, subj, body))

    @models.permalink
    def get_absolute_url(self):
        challenge = self.get_challenge()
        if challenge:
            slug = challenge.slug
        else:
            slug = 'foo'  # TODO - Figure out what to do if no challenges exist
        return ('submission_show', (), {
            'slug': slug,
            'submission_id': self.id,
        })

    def __unicode__(self):
        return u"%s - %s" % (self.title, self.summary)


class VoterTaxonomy(ModelBase):
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.description


class VoterDetails(ModelBase):
    user = models.ForeignKey('users.UserProfile',
                             related_name='voter_details')
    taxonomy = models.ManyToManyField(VoterTaxonomy)


class Judge(ModelBase):
    challenge = models.ForeignKey(Challenge)
    user = models.ForeignKey('users.UserProfile',
                             related_name='judges')

    class Meta:
        unique_together = (('challenge', 'user'),)


### Signals

def submission_markdown_handler(sender, **kwargs):
    submission = kwargs.get('instance', None)
    if not isinstance(submission, Submission):
        return
    if submission.description:
        submission.description_html = bleach.clean(
            markdown(submission.description),
            tags=TAGS, attributes=ALLOWED_ATTRIBUTES)
pre_save.connect(submission_markdown_handler, sender=Submission)
