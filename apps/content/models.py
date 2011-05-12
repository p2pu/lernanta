import logging
import bleach
import datetime

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.signals import pre_save, post_save
from django.template.defaultfilters import truncatewords_html
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import activate, get_language, ugettext
from django.db.models import Max
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

from l10n.urlresolvers import reverse
from drumbeat.models import ModelBase
from activity.models import Activity
from users.tasks import SendUserEmail

log = logging.getLogger(__name__)


class Page(ModelBase):
    """Placeholder model for pages."""
    object_type = 'http://activitystrea.ms/schema/1.0/article'

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110)
    content = models.TextField()
    author = models.ForeignKey('users.UserProfile', related_name='pages')
    last_update = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)
    project = models.ForeignKey('projects.Project', related_name='pages')
    listed = models.BooleanField(default=True)
    collaborative = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)
    index = models.IntegerField()
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('page_show', (), {
            'slug': self.project.slug,
            'page_slug': self.slug,
        })

    def save(self):
        """Make sure each page has a unique url."""
        count = 1
        if not self.slug:
            slug = slugify(self.title)
            self.slug = slug
            while True:
                existing = Page.objects.filter(project__slug=self.project.slug, slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = "%s-%s" % (slug, count + 1)
                count += 1
        if not self.index:
            if self.listed:
                max_index = Page.objects.filter(project=self.project, listed=True).aggregate(Max('index'))['index__max']
                self.index = max_index + 1 if max_index else 1
            else:
                self.index = 0
        super(Page, self).save()

    def timesince(self, now=None):
        return timesince(self.created_on, now)

    def friendly_verb(self):
        return mark_safe(ugettext('added'))

    def representation(self):
        return mark_safe(ugettext(' <a href="%(page_url)s">%(page_title)s</a>.') % dict(page_url=self.get_absolute_url(),
            page_title=escape(self.title)))

    def can_edit(self, user):
        if not self.editable:
            return False
        if self.project.is_organizing(user):
            return True
        if self.collaborative:
            return self.project.is_participating(user)
        return False


class PageVersion(ModelBase):

    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey('users.UserProfile', related_name='page_versions')
    date = models.DateTimeField()
    page = models.ForeignKey('content.Page', related_name='page_versions')
    deleted = models.BooleanField(default=False)

    @models.permalink
    def get_absolute_url(self):
        return ('page_version', (), {
            'slug': self.page.project.slug,
            'page_slug': self.page.slug,
            'version_id': self.id,
        })


class PageComment(ModelBase):
    """Placeholder model for comments."""
    object_type = 'http://activitystrea.ms/schema/1.0/comment'

    content = models.TextField(blank=False)
    author = models.ForeignKey('users.UserProfile', related_name='comments')
    page = models.ForeignKey('content.Page', related_name='comments')
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    reply_to = models.ForeignKey('content.PageComment', blank=True, null=True, related_name='replies')
    abs_reply_to = models.ForeignKey('content.PageComment', blank=True, null=True, related_name='all_replies')
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return _('Comment to %s') % self.page.title

    @models.permalink
    def get_absolute_url(self):
        return ('comment_show', (), {
            'slug': self.page.project.slug,
            'page_slug': self.page.slug,
            'comment_id': self.id,
        })

    @property
    def title(self):
        return ugettext('Comment to %s') % self.page.title

    def timesince(self, now=None):
        return timesince(self.created_on, now)

    def friendly_verb(self):
        return mark_safe(ugettext('posted comment'))

    def representation(self):
        return mark_safe(ugettext(' at <a href="%(comment_url)s">%(page_title)s</a>.') % dict(
            comment_url=self.get_absolute_url(), page_title=escape(self.page.title)))

    @property
    def project(self):
        return self.page.project

    def has_visible_childs(self):
        return self.all_replies.filter(deleted=False).exists()

    def can_edit(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            return (profile == self.author)
        else:
            return False

    def send_sign_up_notification(self):
        """Send sign_up notifications."""
        if self.page.slug != 'sign-up':
            return
        project = self.page.project
        is_answer = not self.reply_to
        ulang = get_language()
        subject = {}
        body = {}
        for l in settings.SUPPORTED_LANGUAGES:
            activate(l[0])
            subject[l[0]] = render_to_string(
                "content/emails/sign_up_updated_subject.txt", {
                'comment': self,
                'is_answer': is_answer,
                'project': project,
                }).strip()
            body[l[0]] = render_to_string(
                "content/emails/sign_up_updated.txt", {
                'comment': self,
                'is_answer': is_answer,
                'project': project,
                'domain': Site.objects.get_current().domain,
                }).strip()
        activate(ulang)
        recipients = {}
        for organizer in project.organizers():
            recipients[organizer.user.username] = organizer.user
        if self.reply_to:
            comment = self
            while comment.reply_to:
                comment = comment.reply_to
                recipients[comment.author.username] = comment.author
        for username in recipients:
            if recipients[username] != self.author:
                pl = recipients[username].preflang or settings.LANGUAGE_CODE
                SendUserEmail.apply_async((recipients[username], subject[pl], body[pl]))


def send_content_notification(instance, is_comment):
    """Send notification when a new page or comment is posted."""
    project = instance.project
    if not is_comment and not instance.listed:
        return
    ulang = get_language()
    subject = {}
    body = {}
    for l in settings.SUPPORTED_LANGUAGES:
        activate(l[0])
        subject[l[0]] = render_to_string(
            "content/emails/content_update_subject.txt", {
            'instance': instance,
            'is_comment': is_comment,
            'project': project,
            }).strip()
        body[l[0]] = render_to_string(
            "content/emails/content_update.txt", {
            'instance': instance,
            'is_comment': is_comment,
            'project': project,
            'domain': Site.objects.get_current().domain,
            }).strip()
    activate(ulang)
    for participation in project.participants():
        if instance.author != participation.user and not participation.no_updates:
            pl = participation.user.preflang or settings.LANGUAGE_CODE
            SendUserEmail.apply_async(
                    (participation.user, subject[pl], body[pl]))


###########
# Signals #
###########


def clean_html(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if isinstance(instance, Page) or isinstance(instance, PageComment):
        log.debug("Cleaning html.")
        if instance.content:
            instance.content = bleach.clean(instance.content,
                tags=settings.RICH_ALLOWED_TAGS, attributes=settings.RICH_ALLOWED_ATTRIBUTES,
                styles=settings.RICH_ALLOWED_STYLES, strip=True)

pre_save.connect(clean_html, sender=Page)
pre_save.connect(clean_html, sender=PageComment)


def fire_activity(sender, **kwargs):
    instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)

    is_page = isinstance(instance, Page)
    is_comment = isinstance(instance, PageComment)
    if created and (is_page or is_comment):
        # Send notification.
        if is_comment and instance.page.slug == 'sign-up':
            instance.send_sign_up_notification()
            return
        else:
            send_content_notification(instance, is_comment)
        # Fire activity.
        activity = Activity(
            actor=instance.author,
            verb='http://activitystrea.ms/schema/1.0/post',
            target_object=instance,
        )
        activity.target_project = instance.project
        activity.save()

post_save.connect(fire_activity, sender=Page)
post_save.connect(fire_activity, sender=PageComment)

