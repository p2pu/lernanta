import logging
import datetime

from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.db.models import Max
from django.contrib.sites.models import Site
from django.contrib.contenttypes import generic
from django.conf import settings

from drumbeat.models import ModelBase
from activity.models import Activity
from activity.schema import verbs, object_types
from notifications.models import send_notifications_i18n
from richtext.models import RichTextField
from replies.models import PageComment
from badges.models import Submission, Award


log = logging.getLogger(__name__)


class Page(ModelBase):
    """Placeholder model for pages."""
    object_type = object_types['article']

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110)
    sub_header = models.CharField(max_length=150, blank=True, null=True)
    content = RichTextField(config_name='rich')
    author = models.ForeignKey('users.UserProfile', related_name='pages')
    last_update = models.DateTimeField(auto_now_add=True,
        default=datetime.datetime.now)
    project = models.ForeignKey('projects.Project', related_name='pages')
    listed = models.BooleanField(default=True)
    minor_update = models.BooleanField(default=True)
    collaborative = models.BooleanField(default=True)
    index = models.IntegerField()
    deleted = models.BooleanField(default=False)

    comments = generic.GenericRelation(PageComment,
        content_type_field='page_content_type',
        object_id_field='page_id')

    # Badges to which the user can submit their work to.
    # Used to facilitate both posting a comment to the task with
    # a link to the work they did on the task and apply for skills badges
    badges_to_apply = models.ManyToManyField('badges.Badge',
        null=True, blank=True, related_name='tasks_accepting_submissions')

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('page_show', (), {
            'slug': self.project.slug,
            'page_slug': self.slug,
        })

    def friendly_verb(self, verb):
        if verbs['post'] == verb:
            return _('added')

    def save(self):
        """Make sure each page has a unique url."""
        count = 1
        if not self.slug:
            slug = slugify(self.title)
            self.slug = slug
            while True:
                existing = Page.objects.filter(
                    project__slug=self.project.slug, slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = "%s-%s" % (slug, count + 1)
                count += 1
        if not self.index:
            if self.listed:
                max_index = Page.objects.filter(project=self.project,
                    listed=True).aggregate(Max('index'))['index__max']
                self.index = max_index + 1 if max_index else 1
            else:
                self.index = 0
        super(Page, self).save()

    def get_next_page(self):
        if self.listed and not self.deleted:
            try:
                return self.project.pages.filter(
                    deleted=False, index__gt=self.index,
                    listed=True).order_by('index')[0]
            except IndexError:
                pass
        return None

    def get_next_badge_can_apply(self, profile):
        next_badges = self.badges_to_apply.order_by('id')
        next_badges_can_apply = []
        for badge in next_badges:
            awarded = Award.objects.filter(user=profile,
                badge=badge).exists()
            applied = Submission.objects.filter(author=profile,
                badge=badge).exists()
            elegible = badge.is_eligible(profile)
            if not awarded and not applied and elegible:
                next_badges_can_apply.append(badge)
            if len(next_badges_can_apply) > 1:
                break
        next_badge = next_badges_can_apply[0] if next_badges_can_apply else None
        is_last_badge = not next_badges_can_apply[1:]
        return next_badge, is_last_badge

    def can_edit(self, user):
        if self.project.is_organizing(user):
            return True
        if self.collaborative:
            return self.project.is_participating(user)
        return False

    def first_level_comments(self):
        return self.comments.filter(reply_to__isnull=True).order_by(
            '-created_on')

    def can_comment(self, user, reply_to=None):
        return self.project.is_participating(user)

    def get_comment_url(self, comment, user):
        comment_index = 0
        abs_reply_to = comment.abs_reply_to or comment
        for first_level_comment in self.first_level_comments():
            if abs_reply_to.id == first_level_comment.id:
                break
            comment_index += 1
        items_per_page = settings.PAGINATION_DEFAULT_ITEMS_PER_PAGE
        page = (comment_index / items_per_page) + 1
        url = self.get_absolute_url()
        return url + '?pagination_page_number=%s#%s' % (
            page, comment.id)

    def comments_fire_activity(self):
        return True

    def comment_notification_recipients(self, comment):
        from users.models import UserProfile
        participants = self.project.participants()
        from_organizer = self.project.organizers().filter(
            user=comment.author).exists()
        if from_organizer:
            participants = participants.filter(
                no_organizers_content_updates=False)
        else:
            participants = participants.filter(
                no_participants_content_updates=False)
        return UserProfile.objects.filter(
            id__in=participants.values('user__id'))

    def recent_activity(self, min_count=2):
        comments = self.comments.filter(deleted=False)
        today = datetime.date.today()
        day = today.day
        month = today.month
        year = today.year
        # get today's commments count
        today_comments_count = comments.filter(created_on__day=day,
            created_on__month=month, created_on__year=year).count()
        if today_comments_count >= min_count:
            return today_comments_count, _('today')
        # get this week comments count
        week = today.isocalendar()[1]
        first_day = datetime.date(year, 1, 1)
        delta_days = first_day.isoweekday() - 1
        delta_weeks = week
        if year == first_day.isocalendar()[0]:
            delta_weeks -= 1
        week_start_delta = datetime.timedelta(days=-delta_days, weeks=delta_weeks)
        week_start = first_day + week_start_delta
        week_end_delta = datetime.timedelta(days=7-delta_days, weeks=delta_weeks)
        week_end = first_day + week_end_delta
        this_week_comments_count = comments.filter(created_on__gte=week_start,
            created_on__lt=week_end).count()
        if this_week_comments_count >= min_count:
            return this_week_comments_count, _('this week')
        # get this month comments count
        this_month_comments_count = comments.filter(created_on__month=month,
            created_on__year=year).count()
        return this_month_comments_count, _('this month')


class PageVersion(ModelBase):

    title = models.CharField(max_length=100)
    sub_header = models.CharField(max_length=150, blank=True, null=True)
    content = RichTextField(config_name='rich', blank=False)
    author = models.ForeignKey('users.UserProfile',
        related_name='page_versions')
    date = models.DateTimeField()
    page = models.ForeignKey('content.Page', related_name='page_versions')
    deleted = models.BooleanField(default=False)
    minor_update = models.BooleanField(default=True)

    @models.permalink
    def get_absolute_url(self):
        return ('page_version', (), {
            'slug': self.page.project.slug,
            'page_slug': self.page.slug,
            'version_id': self.id,
        })


def send_email_notification(instance):
    project = instance.project
    if not instance.listed:
        return
    recipients = project.participants()
    subject_template = 'content/emails/content_update_subject.txt'
    body_template = 'content/emails/content_update.txt'
    context = {
        'instance': instance,
        'project': project,
        'domain': Site.objects.get_current().domain,
    }
    from_organizer = project.organizers().filter(
        user=instance.author).exists()
    profiles = []
    for recipient in recipients:
        profile = recipient.user
        if from_organizer:
            unsubscribed = recipient.no_organizers_content_updates
        else:
            unsubscribed = recipient.no_participants_content_updates
        if instance.author != profile and not unsubscribed:
            profiles.append(profile)
    send_notifications_i18n(profiles, subject_template, body_template, context)


###########
# Signals #
###########


def fire_activity(sender, **kwargs):
    instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    is_page = isinstance(instance, Page)
    if created and is_page:
        send_email_notification(instance)
        # Fire activity.
        activity = Activity(actor=instance.author, verb=verbs['post'],
            target_object=instance, scope_object=instance.project)
        activity.save()
    elif (not created and is_page and not instance.minor_update \
          and not instance.deleted):
        activity = Activity(actor=instance.author, verb=verbs['update'],
            target_object=instance, scope_object=instance.project)
        activity.save()

post_save.connect(fire_activity, sender=Page,
    dispatch_uid='content_page_fire_activity')
