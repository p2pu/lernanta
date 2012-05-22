from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.html import strip_tags
from django.conf import settings

from drumbeat.models import ModelBase, ManagerBase
from activity import schema
from l10n.urlresolvers import reverse
from replies.models import PageComment


FILTERS = {
    'all': lambda activities: activities,
}


def register_filter(name, filter_func):
    FILTERS[name] = filter_func


def apply_filter(activities, name):
    if name in FILTERS:
        return FILTERS[name](activities)
    else:
        return activities


class ActivityManager(ManagerBase):

    def public(self):
        """Get list of activities to show on splash page."""
        remote_object_ct = ContentType.objects.get_for_model(
            RemoteObject)
        from statuses.models import Status
        from projects.models import Project
        status_ct = ContentType.objects.get_for_model(
            Status)
        return Activity.objects.filter(deleted=False,
            scope_object__isnull=False,
            scope_object__not_listed=False,
            scope_object__deleted=False,
            scope_object__test=False).exclude(
            models.Q(target_content_type=remote_object_ct)
            | models.Q(target_content_type=status_ct)
            | models.Q(verb=schema.verbs['follow'])).order_by(
            '-created_on')[:10]

    def dashboard(self, user):
        """
        Given a user, return a list of activities to show on their dashboard.
        """
        projects_following = user.following(model='Project')
        users_following = user.following()
        project_ids = [p.pk for p in projects_following]
        user_ids = [u.pk for u in users_following]
        from projects.models import Project
        return Activity.objects.filter(deleted=False).select_related(
            'actor', 'target_object', 'scope_object').filter(
            models.Q(actor__exact=user) | models.Q(actor__in=user_ids)
          | models.Q(scope_object__in=project_ids)).exclude(
            scope_object__category=Project.CHALLENGE).exclude(
            scope_object__deleted=True).order_by('-created_on')

    def for_user(self, user):
        """Return a list of activities where the actor is user."""
        from projects.models import Project
        return Activity.objects.filter(deleted=False).select_related(
            'actor', 'target_object').filter(
            actor=user).filter(
            models.Q(scope_object__isnull=True)
            | models.Q(scope_object__not_listed=False)).exclude(
            scope_object__category=Project.CHALLENGE).exclude(
            scope_object__deleted=True).order_by('-created_on')


class Activity(ModelBase):
    """Represents a single activity entry."""
    actor = models.ForeignKey('users.UserProfile')
    verb = models.URLField(verify_exists=False)
    target_content_type = models.ForeignKey(ContentType, null=True)
    target_id = models.PositiveIntegerField(null=True)
    target_object = generic.GenericForeignKey('target_content_type',
        'target_id')
    scope_object = models.ForeignKey('projects.Project', null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    # reverse relation for page comments pointing to Activities
    comments = generic.GenericRelation(PageComment,
        content_type_field='page_content_type',
        object_id_field='page_id')

    objects = ActivityManager()

    class Meta:
        verbose_name_plural = _('activities')

    def get_absolute_url(self):
        return reverse('activity_index',
            kwargs={'activity_id': self.pk})

    def textual_representation(self):
        return _('%(actor)s %(verb)s %(target)s') % dict(
                actor=self.actor, verb=self.friendly_verb(),
                target=strip_tags(unicode(self.target_object)))

    def friendly_verb(self):
        verb = None
        if hasattr(self.target_object, 'friendly_verb'):
            verb = self.target_object.friendly_verb(self.verb)
        verb = verb or schema.past_tense[schema.verbs_by_uri[self.verb]]
        return verb

    def html_representation(self):
        return render_to_string('activity/_activity_body.html', {
            'activity': self,
            'show_actor': True,
        })

    def __unicode__(self):
        return _('wall activity from %s') % self.actor

    def can_edit(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            return (profile == self.actor)
        else:
            return False

    def visible_replies(self):
        return self.comments.filter(deleted=False)

    def first_level_comments(self):
        return self.comments.filter(reply_to__isnull=True).order_by(
            '-created_on')

    def can_comment(self, user, reply_to=None):
        if user.is_authenticated():
            if self.scope_object:
                return self.scope_object.is_participating(user)
            else:
                can_reply = (user.get_profile() == self.actor)
                can_reply = can_reply or self.actor.is_following(user)
                if reply_to:
                    can_reply = can_reply or reply_to.author.is_following(user)
                return can_reply
        return False

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
        if self.scope_object:
            from users.models import UserProfile
            participants = self.scope_object.participants()
            from_organizer = self.scope_object.organizers().filter(
                user=comment.author).exists()
            if from_organizer:
                participants = participants.filter(
                    no_organizers_wall_updates=False)
            else:
                participants = participants.filter(
                    no_participants_wall_updates=False)
            return UserProfile.objects.filter(
                id__in=participants.values('user__id'))
        else:
            recipients = {self.actor.username: self.actor}
            while comment.reply_to:
                comment = comment.reply_to
                recipients[comment.author.username] = comment.author
            return recipients.values()


class RemoteObject(models.Model):
    """Represents an object originating from another system."""
    object_type = models.URLField(verify_exists=False)
    link = models.ForeignKey('links.Link')
    title = models.CharField(max_length=255)
    uri = models.URLField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    activity = generic.GenericRelation(Activity,
        content_type_field='target_content_type',
        object_id_field='target_id')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.uri

    @staticmethod
    def filter_activities(activities):
        ct = ContentType.objects.get_for_model(RemoteObject)
        return activities.filter(target_content_type=ct)

register_filter('subscriptions', RemoteObject.filter_activities)
