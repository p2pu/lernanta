import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site

from drumbeat.models import ModelBase
from activity.schema import verbs, object_types
from tracker import statsd
from notifications.models import send_notifications_i18n
from l10n.urlresolvers import reverse

from richtext.models import RichTextField

class PageComment(ModelBase):
    """Placeholder model for comments."""
    object_type = object_types['comment']

    content = RichTextField(config_name='rich', blank=False)
    author = models.ForeignKey('users.UserProfile',
        related_name='comments')

    # the comments can live inside a project, a school, or just be associated
    # with their author
    scope_content_type = models.ForeignKey(ContentType, null=True,
        related_name='scope_page_comments')
    scope_id = models.PositiveIntegerField(null=True)
    scope_object = generic.GenericForeignKey('scope_content_type',
        'scope_id')

    # object to which the comments are associated (a task, a signup answer,
    # an activity on the wall, ...)
    page_content_type = models.ForeignKey(ContentType, null=True)
    page_id = models.PositiveIntegerField(null=True)
    page_object = generic.GenericForeignKey('page_content_type',
        'page_id')

    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    reply_to = models.ForeignKey('replies.PageComment', blank=True,
        null=True, related_name='replies')
    abs_reply_to = models.ForeignKey('replies.PageComment', blank=True,
        null=True, related_name='all_replies')
    deleted = models.BooleanField(default=False)

    # indicate that a comment was sent via email
    sent_by_email = models.BooleanField(default=False, blank=True)

    def __unicode__(self):
        return _('comment at %s') % self.page_object

    @models.permalink
    def get_absolute_url(self):
        return ('comment_show', (), {
            'comment_id': self.id,
        })

    def has_visible_childs(self):
        return self.visible_replies().exists()

    def visible_replies(self):
        return self.all_replies.filter(deleted=False).order_by('created_on')

    def can_edit(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            return (profile == self.author)
        else:
            return False

    def reply(self, user, reply_body, sent_by_email = False):
        """ Create a reply from user to this comment """
        # TODO check if user can reply
        
        reply_comment = PageComment()
        reply_comment.author = user
        reply_comment.content = reply_body

        reply_comment.page_object = self.page_object
        reply_comment.scope_object = self.scope_object
        reply_comment.reply_to = self
        reply_comment.abs_reply_to = self.abs_reply_to or self
        reply_comment.sent_by_email = sent_by_email
        reply_comment.save()
        # NOTE: comments deprecated
        # reply_comment.send_comment_notification()
        return reply_comment

    def send_comment_notification(self):
        recipients = []
        if self.page_object:
            recipients = self.page_object.comment_notification_recipients(self)
        subject_template = 'replies/emails/post_comment_subject.txt'
        body_template = 'replies/emails/post_comment.txt'
        context = {
            'comment': self,
            'domain': Site.objects.get_current().domain,
        }
        profiles = []
        for profile in recipients:
            if self.author != profile:
                profiles.append(profile)
        reply_url = reverse('email_reply', args=[self.id])

        notification_category='reply'
        from projects.models import Project
        ct = ContentType.objects.get_for_model(Project)
        if self.scope_object and self.scope_content_type == ct:
            notification_category='reply.project-{0}'.format(self.scope_object.slug)

        send_notifications_i18n(profiles, subject_template, body_template, context,
            reply_url, self.author.username,
            notification_category=notification_category
        )


###########
# Signals #
###########

def fire_activity(sender, **kwargs):
    instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    is_comment = isinstance(instance, PageComment)
    if created and is_comment:
        from signups.models import SignupAnswer
        ct = ContentType.objects.get_for_model(SignupAnswer)
        if instance.page_content_type != ct:
            statsd.Statsd.increment('comments')
        if instance.page_object and instance.page_object.comments_fire_activity():
            from activity.models import Activity
            activity = Activity(actor=instance.author, verb=verbs['post'],
                target_object=instance, scope_object=instance.scope_object)
            activity.save()

post_save.connect(fire_activity, sender=PageComment,
    dispatch_uid='replies_pagecomment_fire_activity')


def create_comment( comment_text, user_uri ):
    # TODO: comments should only use user_uri
    from users.models import UserProfile
    username = user_uri.strip('/').split('/')[-1]
    user = UserProfile.objects.get(username=username)

    comment = PageComment()
    comment.author = user
    comment.content = comment_text
    comment.sent_by_email = False
    comment.save()
    # TODO: comment.send_comment_notification()
    return get_comment("/uri/comment/{0}".format(comment.id))


def get_comment( comment_uri, limit_replies=-1 ):
    comment_id = comment_uri.strip('/').split('/')[-1]
    try:
        comment_db = PageComment.objects.get(id=comment_id)
    except:
        return None

    comment = {
        "id": comment_db.id,
        "uri": "/uri/comment/{0}".format(comment_db.id),
        "content": comment_db.content,
        "user_uri": "/uri/user/{0}".format(comment_db.author.username),
        "replies": []
    }

    if limit_replies != 0:
        replies = comment_db.replies.all().order_by("-created_on")
        if limit_replies > 0:
            replies = replies[:limit_replies]

        for reply in replies:
            comment['replies'] += [{
                "id": reply.id,
                "uri": "/uri/comment/{0}".format(reply.id),
                "content": reply.content,
                "user_uri": "/uri/user/{0}".format(reply.author.username),
            }]
    return comment


def reply_to_comment( comment_uri, comment_content, user_uri ):
    # TODO: comments should only use user_uri
    from users.models import UserProfile
    username = user_uri.strip('/').split('/')[-1]
    user = UserProfile.objects.get(username=username)

    comment_id = comment_uri.strip('/').split('/')[-1]
    try:
        comment_db = PageComment.objects.get(id=comment_id)
    except:
        return None

    reply = comment_db.reply(user, comment_content)
    return get_comment("/uri/comment/{0}".format(reply.id))

