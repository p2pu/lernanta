import datetime

from django.db import models
from django.conf import settings
from django.db.models import Avg, Q
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save
from django.contrib.sites.models import Site

from drumbeat import storage
from drumbeat.utils import get_partition_id, safe_filename, MultiQuerySet
from drumbeat.models import ModelBase
from richtext.models import RichTextField
from notifications.models import send_notifications
from l10n.urlresolvers import reverse


def determine_upload_path(instance, filename):
    chunk_size = 1000  # max files per directory
    return "images/badges/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk, chunk_size),
        'filename': safe_filename(filename),
    }


def get_awarded_badges(user):
    from pilot import get_awarded_badges as get_pilot_badges
    badges = get_pilot_badges(user)
    profile = user.get_profile()
    badges_ids = Award.objects.filter(user=profile).values(
        'badge_id').distinct()
    for badge in Badge.objects.filter(id__in=badges_ids):
        evidence = reverse('user_awards_show',
            kwargs= dict(slug=badge.slug, username=profile.username))
        awards_count = Award.objects.filter(user=profile,
             badge=badge).count()
        data = {
            'name': badge.name,
            'description': badge.description,
            'image': badge.get_image_url(),
            'evidence': evidence,
            'criteria': badge.get_absolute_url(),
            'count': awards_count,
        }
        badges[badge.slug] = data
    return badges


class Badge(ModelBase):
    """Representation of a Badge"""
    name = models.CharField(max_length=225, blank=False)
    slug = models.SlugField(unique=True, max_length=110)
    description = models.CharField(max_length=225, blank=False)
    requirements = RichTextField(blank=True, null=True)
    image = models.ImageField(
        upload_to=determine_upload_path, default='', blank=True, null=True,
        storage=storage.ImageStorage())
    prerequisites = models.ManyToManyField('self', symmetrical=False,
        blank=True, null=True)
    rubrics = models.ManyToManyField('badges.Rubric', related_name='badges',
        null=True, blank=True)
    logic = models.ForeignKey('badges.Logic', related_name='badges',
        help_text=_('Regulates how the badge is awarded to users.'))
    all_groups = models.BooleanField(default=False)
    groups = models.ManyToManyField('projects.Project', related_name='badges',
        null=True, blank=True)
    creator = models.ForeignKey('users.UserProfile', related_name='badges',
        blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=False)

    def __unicode__(self):
        return "%s %s" % (self.name, _('Badge'))

    @models.permalink
    def get_absolute_url(self):
        return ('badges_show', (), {
            'slug': self.slug,
        })

    def get_image_url(self):
        # TODO: using project's default image until a default badge
        # image is added.
        missing = settings.STATIC_URL + 'images/missing-badge.png'
        image_path = self.image.url if self.image else missing
        return image_path

    def save(self):
        """Make sure each badge has a unique slug."""
        count = 1
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug
            while True:
                existing = Badge.objects.filter(slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = "%s-%s" % (slug, count + 1)
                count += 1
        super(Badge, self).save()

    def is_eligible(self, user):
        """Check if the user eligible for the badge.

        If some prerequisite badges have not been
        awarded returns False."""
        awarded_badges = Award.objects.filter(
            user=user).values('badge_id')
        return not self.prerequisites.exclude(
            id__in=awarded_badges).exists()

    def is_awarded_to(self, user):
        """Does the user have the badge?"""
        return Award.objects.filter(user=user, badge=self).count() > 0

    def award_to(self, user, submission=None):
        """Award the badge to the user.

        Returns None if no badge is awarded."""

        if not self.is_eligible(user):
            # If the user is not eligible the badge
            # is not awarded.
            return None

        if self.pending_peer_reviews(user, submission):
            # The user has not received the necessary satisfactory reviews
            # for the badge to be awarded.
            return None

        if submission:
            submission.pending = False
            submission.save()

        if self.logic.unique:
            # Do not award the badge if the user can not have the badge
            # more than once and it was already awarded.
            award, created = Award.objects.get_or_create(user=user,
                badge=self)
            return award if created else None

        return Award.objects.create(user=user, badge=self)

    def pending_peer_reviews(self, user, submission):
        if not self.logic.min_votes:
            return False
        assessments = Assessment.objects.filter(badge=self,
            assessed=user, ready=True)
        if submission:
            assessments = assessments.filter(submission=submission)
        else:
            assessments = assessments.filter(submission__isnull=True)
        if assessments.count() < self.logic.min_votes:
            # More votes needed.
            return True
        if not self.logic.min_avg_rating:
            return False
        avg_rating = Assessment.compute_average_rating(assessments)
        if avg_rating < self.logic.min_avg_rating:
            # Rating too low.
            return True

    def get_pending_submissions(self):
        """Submissions of users who haven't received the award yet"""
        return Submission.objects.filter(badge=self, pending=True)

    def get_peers(self, profile):
        from projects.models import Participation
        from users.models import UserProfile
        user_projects = Participation.objects.filter(
            user=profile).values('project__id')
        peers = Participation.objects.filter(
            project__in=user_projects)
        if not self.all_groups:
            badge_projects = self.groups.values('id')
            peers = peers.filter(project__in=badge_projects)
        return UserProfile.objects.filter(deleted=False,
            id__in=peers.values('user__id')).exclude(
            id=profile.id)

    def other_badges_can_apply_for(self):
        badges = Badge.objects.exclude(
            id=self.id).exclude(
            logic__submission_style=Logic.NO_SUBMISSIONS)
        badge_groups = self.groups.values('id')
        related_badges = badges.filter(
            groups__in=badge_groups).distinct()
        non_related_badges = badges.exclude(
            groups__in=badge_groups).distinct()
        return MultiQuerySet(related_badges, non_related_badges)

    def can_post_submission(self, user):
        if self.logic.submission_style == Logic.NO_SUBMISSIONS:
            return False
        if user.is_authenticated():
            profile = user.get_profile()
            if not self.is_eligible(profile):
                return False
            awards = Award.objects.filter(user=profile, badge=self)
            if self.logic.unique and awards.exists():
                return False
            return True
        else:
            return False

    def can_give_to_peer(self, user):
        if not user.is_authenticated():
            return False
        if self.logic.submission_style == Logic.SUBMISSION_REQUIRED:
            return False
        if self.logic.min_votes != 1 or self.logic.min_avg_rating > 0:
            return False
        return True

    def can_review_submission(self, submission, user):
        # only authenticated users can review a submission
        if not user.is_authenticated():
            return False
        profile = user.get_profile()

        # user cannot review his/her own submission
        if profile == submission.author:
            return False

        # if this is a unique badge, only allow one review of submission
        if self.logic.unique and not submission.pending:
            return False

        # user can only submit one review
        assessments = submission.assessments.filter(
            assessor=profile)
        if assessments.exists():
            return False

        return True

    def get_adopters(self):
        from projects.models import Participation
        from users.models import UserProfile
        adopters = Participation.objects.filter(
            project__in=self.groups.values('id'),
            left_on__isnull=True).filter(
            Q(adopter=True) | Q(organizing=True)).values(
            'user_id').distinct()
        return UserProfile.objects.filter(id__in=adopters)


class Rubric(ModelBase):
    """Criteria for which a badge application is judged"""
    question = models.CharField(max_length=200)

    def __unicode__(self):
        return self.question


class Logic(ModelBase):
    """Representation of the logic behind awarding a badge"""
    name = models.CharField(max_length=40)
    min_votes = models.PositiveIntegerField(
        help_text=_('Minimum number of votes.'),
        default=0)
    min_avg_rating = models.PositiveIntegerField(
        help_text=_('Minimum average rating.'),
        default=0)
    unique = models.BooleanField(
        help_text=_('If the badge can only be awarded to the user once.'),
        default=False)
    SUBMISSION_REQUIRED = 'submission_required'
    SUBMISSION_OPTIONAL = 'submission_optional'
    NO_SUBMISSIONS = 'no_submissions'
    SUBMISSION_STYLE_CHOICES = (
        (SUBMISSION_REQUIRED, _('Submission Required')),
        (SUBMISSION_OPTIONAL, _('Submission Optional')),
        (NO_SUBMISSIONS, _('No submissions'))
    )
    submission_style = models.CharField(max_length=30,
        choices=SUBMISSION_STYLE_CHOICES,
        default=NO_SUBMISSIONS)

    def __unicode__(self):
        return self.name


class Submission(ModelBase):
    """Application for a badge"""
    # TODO Refactor this and PageComment and Assessment?
    # to extend off same base
    url = models.URLField(max_length=1023)
    content = RichTextField(config_name='rich', blank=False)
    author = models.ForeignKey('users.UserProfile', related_name='submissions')
    badge = models.ForeignKey('badges.Badge', related_name="submissions")
    created_on = models.DateTimeField(auto_now_add=True,
        default=datetime.datetime.now)
    pending = models.BooleanField(default=True)

    def __unicode__(self):
        return _('%(author)s\'s application for %(badge)s') % {
            'author': self.author, 'badge': self.badge}

    @models.permalink
    def get_absolute_url(self):
        return ('submission_show', (), {
            'slug': self.badge.slug,
            'submission_id': self.id,
        })

    def send_notification(self):
        """Send notification when a new submission is posted."""
        subject_template = 'badges/emails/new_submission_subject.txt'
        body_template = 'badges/emails/new_submission.txt'
        context = {
            'submission': self,
            'domain': Site.objects.get_current().domain,
        }
        profiles = self.badge.get_adopters()
        send_notifications(profiles, subject_template, body_template, context)


class Assessment(ModelBase):
    """Assessment for a badge"""
    final_rating = models.FloatField(default=0)
    weight = models.FloatField(default=1,
        help_text=_("Allows to give more or less weight to the assessor's vote."))
    assessor = models.ForeignKey('users.UserProfile',
        related_name='assessments')
    assessed = models.ForeignKey('users.UserProfile',
        related_name='badge_assessments')
    comment = RichTextField(config_name='rich', blank=False)
    badge = models.ForeignKey('badges.Badge', related_name="assessments")
    created_on = models.DateTimeField(auto_now_add=True,
        default=datetime.datetime.now)
    submission = models.ForeignKey('badges.Submission',
        related_name="assessments", null=True, blank=True,
        help_text=_('If submission is blank, this is a '\
        'peer awarded assessment or superuser granted'))
    ready = models.BooleanField(default=False,
        help_text=_("If all rubric ratings were provided."))

    def __unicode__(self):
        return _('%(assessor)s for %(assessed)s for %(badge)s') % {
            'assessor': self.assessor, 'assessed': self.assessed,
            'badge': self.badge}

    @models.permalink
    def get_absolute_url(self):
        return ('assessment_show', (), {
            'slug': self.badge.slug,
            'assessment_id': self.id,
        })

    def final_rating_as_percentage(self):
        """Return the final rating as a percentage for
        styling of assessment view. Max number of ratings
        is 4"""
        return (self.final_rating / 4.0) * 100

    def get_final_rating_display(self):
        rating_position = int(round(self.final_rating)) - 1
        # Guarantee rating_position does not go above or below
        # the boundaries.
        if rating_position < 0:
            rating_position = 0
        max_index = len(Rating.RATING_CHOICES) - 1
        if rating_position > max_index:
            rating_position = max_index
        return Rating.RATING_CHOICES[rating_position][1]

    def update_final_rating(self):
        """Used on Rating save signal to update the final
        rating for the assessment"""
        if self.ready:
            return
        ratings = Rating.objects.filter(assessment=self)
        self.final_rating = ratings.aggregate(
            final_rating=Avg('score'))['final_rating'] or 0
        if ratings.count() == self.badge.rubrics.count():
            self.ready = True
        self.save()
        if self.submission and not self.submission.pending:
            return
        if self.ready:
            self.badge.award_to(self.assessed, self.submission)

    @classmethod
    def compute_average_rating(cls, assessments):
        ratings_sum = 0
        weights_sum = 0
        for assessment in assessments:
            ratings_sum += assessment.final_rating
            weights_sum += assessment.weight
        return ratings_sum / weights_sum if weights_sum > 0 else 0


class Rating(ModelBase):
    """Assessor's rating for the assessment's rubric(s)"""

    NEVER = 1
    SOMETIMES = 2
    MOST_OF_THE_TIME = 3
    ALWAYS = 4

    RATING_CHOICES = (
        (NEVER, _('Never')),
        (SOMETIMES, _('Sometimes')),
        (MOST_OF_THE_TIME, _('Most of the time')),
        (ALWAYS, _('Always'))
    )

    assessment = models.ForeignKey('badges.Assessment', related_name='ratings')
    score = models.PositiveIntegerField(default=1, choices=RATING_CHOICES)
    rubric = models.ForeignKey('badges.Rubric', related_name='ratings')

    def __unicode__(self):
        return _('%(score)s for %(rubric)s') % {
            'score': self.score,
            'rubric': self.rubric
        }

    def score_as_percentage(self):
        """Return the score as a percentage for
        styling of assessment view. Max number of ratings
        is 4"""
        return (self.score / 4.0) * 100


class Award(ModelBase):
    """Representation of a badge a user has received"""
    user = models.ForeignKey('users.UserProfile')
    badge = models.ForeignKey('badges.Badge', related_name="awards")
    awarded_on = models.DateTimeField(auto_now_add=True, blank=False)

    def __unicode__(self):
        return _('%(user)s - %(badge)s') % {'user': self.user,
            'badge': self.badge}

    @models.permalink
    def get_absolute_url(self):
        # All the awards of the same badge to the same user
        # share one awards page.
        return ('user_awards_show', (), {
            'slug': self.badge.slug,
            'username': self.user.username,
        })


###########
# Signals #
###########


def post_submission_save(sender, **kwargs):
    instance = kwargs.get('instance', None)
    created = kwargs.get('created', False)
    if created and isinstance(instance, Submission):
        instance.send_notification()

post_save.connect(post_submission_save, sender=Submission,
    dispatch_uid='badges_post_submission_save')
