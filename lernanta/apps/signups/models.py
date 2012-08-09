import datetime

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.conf import settings

from notifications.models import send_notifications
from drumbeat.models import ModelBase
from richtext.models import RichTextField
from activity.schema import object_types
from replies.models import PageComment
from projects.models import Participation


class Signup(ModelBase):
    project = models.ForeignKey('projects.Project', related_name='sign_up')
    public = RichTextField(config_name='rich', blank=True)
    between_participants = RichTextField(config_name='rich', blank=True)
    author = models.ForeignKey('users.UserProfile')

    MODERATED = 'moderated'
    NON_MODERATED = 'non-moderated'
    CLOSED = 'closed'
    STATUS_CHOICES = (
        (CLOSED, _('Closed signup')),
        (MODERATED, _('Moderated signup')),
        (NON_MODERATED, _('Non-moderated signup')),
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,
        default=CLOSED, null=True, blank=False)

    @models.permalink
    def get_absolute_url(self):
        return ('sign_up', (), {
            'slug': self.project.slug,
        })

    @property
    def standard(self):
        return render_to_string('signups/sign_up_initial_content.html',
            {'project': self.project})

    def pending_answers(self):
        return self.answers.filter(accepted=False, deleted=False)

    def get_visible_answers(self, user):
        answers = self.answers.all()
        if user.is_authenticated():
            profile = user.get_profile()
            is_organizing = self.project.organizers().filter(
                user=profile).exists()
            if not is_organizing:
                answers = answers.filter(Q(accepted=True) | Q(author=profile))
        else:
            answers = answers.filter(accepted=True)
        return answers.order_by('-created_on')

    def get_page_for_answer(self, answer, user):
        answer_index = 0
        for visible_answer in self.get_visible_answers(user):
            if visible_answer.id == answer.id:
                break
            answer_index += 1
        items_per_page = settings.PAGINATION_DEFAULT_ITEMS_PER_PAGE
        return (answer_index / items_per_page) + 1

    def get_answer_url(self, answer, user):
        page = self.get_page_for_answer(answer, user)
        url = self.get_absolute_url()
        return url + '?pagination_page_number=%s#answer-%s' % (
            page, answer.id)

    def set_unmoderated_signup(self):
        self.status = self.NON_MODERATED
        self.save()

    def is_closed(self):
        return self.status == self.CLOSED


class SignupAnswer(ModelBase):
    object_type = object_types['comment']
    sign_up = models.ForeignKey('signups.Signup', related_name='answers')
    standard = RichTextField(config_name='rich', blank=False)
    public = RichTextField(config_name='rich', blank=True)
    between_participants = RichTextField(config_name='rich', blank=True)
    author = models.ForeignKey('users.UserProfile',
        related_name='sigup_answers')
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    accepted = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    comments = generic.GenericRelation(PageComment,
        content_type_field='page_content_type',
        object_id_field='page_id')

    def __unicode__(self):
        return _("the signup answer of %(author)s at %(project)s") % {
            'author': self.author, 'project': self.project}

    @property
    def project(self):
        return self.sign_up.project

    @models.permalink
    def get_absolute_url(self):
        return ('show_signup_answer', (), {
            'slug': self.project.slug,
            'answer_id': self.id,
        })

    def can_edit(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            return (profile == self.author)
        else:
            return False

    def first_level_comments(self):
        return self.comments.filter(reply_to__isnull=True).order_by(
            'created_on')

    def has_visible_childs(self):
        return self.comments.filter(deleted=False).exists()

    def can_comment(self, user, reply_to=None):
        if user.is_authenticated():
            if self.accepted:
                return self.project.is_participating(user)
            else:
                is_organizing = self.project.is_organizing(user)
                profile = user.get_profile()
                return is_organizing or (profile == self.author)
        else:
            return False

    def get_comment_url(self, comment, user):
        page = self.sign_up.get_page_for_answer(self, user)
        url = self.sign_up.get_absolute_url()
        return url + '?pagination_page_number=%s#%s' % (
            page, comment.id)

    def comments_fire_activity(self):
        return False

    def comment_notification_recipients(self, comment):
        project = self.project
        recipients = {self.author.username: self.author}
        for organizer in project.organizers():
            recipients[organizer.user.username] = organizer.user
        while comment.reply_to:
            comment = comment.reply_to
            recipients[comment.author.username] = comment.author
        return recipients.values()

    def accept(self, as_organizer=False, reviewer=None):
        if not reviewer:
            reviewer = self.sign_up.author
        is_organizing = self.project.organizers().filter(
            user=self.author).exists()
        is_participating = self.project.participants().filter(
            user=self.author).exists()
        if not is_organizing and not is_participating:
            participation = Participation(project=self.project,
                user=self.author, organizing=as_organizer)
            participation.save()
        accept_content = render_to_string(
            "signups/accept_sign_up_comment.html",
            {'as_organizer': as_organizer})
        accept_comment = PageComment(content=accept_content,
            author=reviewer, page_object=self, scope_object=self.project)
        accept_comment.save()
        self.accepted = True
        self.save()


def send_new_signup_answer_notification(answer):
    recipients = answer.sign_up.project.organizers()
    subject_template = 'signups/emails/new_signup_answer_subject.txt'
    body_template = 'signups/emails/new_signup_answer.txt'
    context = {
        'answer': answer,
        'domain': Site.objects.get_current().domain,
    }
    profiles = [recipient.user for recipient in recipients]
    send_notifications(profiles, subject_template, body_template, context)


###########
# Signals #
###########


def post_save_answer(sender, **kwargs):
    instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    is_answer = isinstance(instance, SignupAnswer)
    if created and is_answer:
        send_new_signup_answer_notification(instance)


post_save.connect(post_save_answer, sender=SignupAnswer,
    dispatch_uid='signups_post_save_answer')
