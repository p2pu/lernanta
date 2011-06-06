import os
import logging
import datetime
import bleach

from django.core.cache import cache
from django.core.validators import MaxLengthValidator
from django.conf import settings
from django.db import models
from django.db.models import Count, Q, Max
from django.db.models.signals import pre_save, post_save, post_delete 
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as ugettex, get_language, activate
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.mail import send_mail

from drumbeat import storage
from drumbeat.utils import get_partition_id, safe_filename
from drumbeat.models import ModelBase
from relationships.models import Relationship
from content.models import Page
from activity.models import Activity
from users.tasks import SendUserEmail

from projects.tasks import ThumbnailGenerator

import caching.base
 
log = logging.getLogger(__name__)


def determine_image_upload_path(instance, filename):
    return "images/projects/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk),
        'filename': safe_filename(filename),
    }


class ProjectManager(caching.base.CachingManager):

    def get_popular(self, limit=0, school=None):
        popular = cache.get('projectspopular')
        if not popular:
            rels = Relationship.objects.values('target_project').annotate(
                Count('id')).exclude(target_project__isnull=True).filter(
                target_project__under_development=False,
                target_project__not_listed=False,
                target_project__archived=False).order_by('-id__count')
            if school:
                rels = rels.filter(target_project__school=school).exclude(
                    target_project__id__in=school.declined.values('id'))
            if limit:
                rels = rels[:limit]
            popular = [r['target_project'] for r in rels]
            cache.set('projectspopular', popular, 3000)
        return Project.objects.filter(id__in=popular)

    def get_active(self, limit=0, school=None):
        active = cache.get('projectsactive')
        if not active:
            activities = Activity.objects.values('target_project').annotate(
                Max('created_on')).exclude(target_project__isnull=True,
                verb='http://activitystrea.ms/schema/1.0/follow',
                remote_object__isnull=False).filter(target_project__under_development=False,
                target_project__not_listed=False,
                target_project__archived=False).order_by('-created_on__max')
            if school:
                activities = activities.filter(target_project__school=school).exclude(
                    target_project__id__in=school.declined.values('id'))
            if limit:
                activities = activities[:limit]
            active = [a['target_project'] for a in activities]
            cache.set('projectsactive', active, 3000)
        return Project.objects.filter(id__in=active)


class Project(ModelBase):
    """Placeholder model for projects."""
    object_type = 'http://drumbeat.org/activity/schema/1.0/project'
    generalized_object_type = 'http://activitystrea.ms/schema/1.0/group'

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=30, default=_('Study Group'))
    short_description = models.CharField(max_length=150)
    long_description = models.TextField(validators=[MaxLengthValidator(700)])
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    school = models.ForeignKey('schools.School', related_name='projects', null=True, blank=True)

    detailed_description = models.ForeignKey('content.Page', related_name='desc_project', null=True, blank=True)
    sign_up = models.ForeignKey('content.Page', related_name='sign_up_project', null=True, blank=True)

    image = models.ImageField(upload_to=determine_image_upload_path, null=True,
                              storage=storage.ImageStorage(), blank=True)

    slug = models.SlugField(unique=True, max_length=110)
    featured = models.BooleanField(default=False)
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)

    under_development = models.BooleanField(default=True)
    not_listed = models.BooleanField(default=False)
    signup_closed = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)

    clone_of = models.ForeignKey('projects.Project', blank=True, null=True,
        related_name='derivated_projects')

    imported_from = models.CharField(max_length=150, blank=True, null=True)

    objects = ProjectManager()

    class Meta:
        verbose_name = _('group')

    def followers(self):
        return Relationship.objects.filter(target_project=self, source__deleted=False)

    def non_participant_followers(self):
        return self.followers().exclude(
            source__id__in=self.participants().values('user_id'))

    def participants(self):
        """Return a list of users participating in this project."""
        return Participation.objects.filter(project=self,
            left_on__isnull=True, user__deleted=False)

    def pending_applicants(self):
        page = self.sign_up
        users = []
        first_level_comments = page.comments.filter(reply_to__isnull=True)
        for answer in first_level_comments.filter(deleted=False):
            if not self.participants().filter(user=answer.author).exists() and not answer.author.deleted:
                users.append(answer.author)
        return users

    def non_organizer_participants(self):
        return self.participants().filter(organizing=False)

    def organizers(self):
        return self.participants().filter(organizing=True)

    def is_organizing(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            is_organizer = self.organizers().filter(user=profile).exists()
            is_superuser = user.is_superuser
            return is_organizer or is_superuser
        else:
            return False

    def is_following(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            is_following = self.followers().filter(source=profile).exists()
            return is_following
        else:
            return False

    def is_participating(self, user):
        if user.is_authenticated():
            profile = user.get_profile()
            is_organizer_or_participant = self.participants().filter(user=profile).exists()
            is_superuser = user.is_superuser
            return is_organizer_or_participant or is_superuser
        else:
            return False

    def is_pending_signup(self, user):
        for applicant in self.pending_applicants():
            if applicant == user:
                return True
        return False

    def activities(self):
        activities = Activity.objects.filter(deleted=False).filter(
            Q(project=self) | Q(target_project=self),
        ).exclude(
            verb='http://activitystrea.ms/schema/1.0/follow'
        ).order_by('-created_on')
        return activities

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('projects_show', (), {
            'slug': self.slug,
        })

    def create(self):
        self.save()
        self.send_creation_notification()

    def save(self):
        """Make sure each project has a unique slug."""
        count = 1
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug
            while True:
                existing = Project.objects.filter(slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = "%s-%s" % (slug, count + 1)
                count += 1
        super(Project, self).save()

    def get_image_url(self):
        missing = settings.MEDIA_URL + 'images/project-missing.png'
        image_path = self.image.url if self.image else missing
        return image_path

    def send_creation_notification(self):
        """Send notification when a new project is created."""
        project = self
        ulang = get_language()
        subject = {}
        body = {}
        domain = Site.objects.get_current().domain
        for l in settings.SUPPORTED_LANGUAGES:
            activate(l[0])
            subject[l[0]] = render_to_string(
                "projects/emails/project_created_subject.txt", {
                'project': project,
                }).strip()
            body[l[0]] = render_to_string(
                "projects/emails/project_created.txt", {
                'project': project,
                'domain': domain,
                }).strip()
        activate(ulang)
        for organizer in project.organizers():
            if not organizer.no_updates:
                ol = organizer.user.preflang or settings.LANGUAGE_CODE
                SendUserEmail.apply_async(
                        (organizer.user, subject[ol], body[ol]))
        admin_subject = render_to_string(
            "projects/emails/admin_project_created_subject.txt", {
            'project': project,
            }).strip()
        admin_body = render_to_string(
            "projects/emails/admin_project_created.txt", {
            'project': project,
            'domain': domain,
            }).strip()
        admin_email = settings.ADMIN_PROJECT_CREATE_EMAIL
        send_mail(admin_subject, admin_body, admin_email, [admin_email], fail_silently=True)

    def accepted_school(self):
        school = self.school
        if school and school.declined.filter(id=self.id).exists():
            school = None
        return school


class Participation(ModelBase):
    user = models.ForeignKey('users.UserProfile', related_name='participations')
    project = models.ForeignKey('projects.Project', related_name='participations')
    organizing = models.BooleanField(default=False)
    joined_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    left_on = models.DateTimeField(blank=True, null=True)
    # The user can configure this preference but the organizer can by pass
    # it with the contact participant form.
    no_wall_updates = models.BooleanField(default=False)
    # for new pages or comments.
    no_updates = models.BooleanField(default=False) 


###########
# Signals #
###########

def clean_html(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if isinstance(instance, Project):
        log.debug("Cleaning html.")
        if instance.long_description:
            instance.long_description = bleach.clean(instance.long_description,
                tags=settings.REDUCED_ALLOWED_TAGS, attributes=settings.REDUCED_ALLOWED_ATTRIBUTES, strip=True)
            

pre_save.connect(clean_html, sender=Project)

