import logging

from django.db import models
from django.template.defaultfilters import slugify
from django.db.models import Q
from django.conf import settings

from drumbeat.models import ModelBase
from drumbeat.utils import get_partition_id, safe_filename
from drumbeat import storage
from richtext.models import RichTextField
from users.models import UserProfile
from badges.models import Badge


log = logging.getLogger(__name__)


def schools_determine_image_upload_path(instance, filename):
    return "images/schools/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk),
        'filename': safe_filename(filename),
    }


class School(ModelBase):
    """Placeholder model for schools."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    short_name = models.CharField(max_length=20)
    description = RichTextField(config_name='rich')
    more_info = RichTextField(config_name='rich', null=True, blank=True)
    organizers = models.ManyToManyField('users.UserProfile',
        null=True, blank=True)
    featured = models.ManyToManyField('projects.Project',
        related_name='school_featured', null=True, blank=True)

    logo = models.ImageField(upload_to=schools_determine_image_upload_path, null=True,
                              storage=storage.ImageStorage(), blank=True)
    groups_icon = models.ImageField(upload_to=schools_determine_image_upload_path,
        null=True, storage=storage.ImageStorage(), blank=True)
    background = models.ImageField(upload_to=schools_determine_image_upload_path,
        null=True, storage=storage.ImageStorage(), blank=True)
    site_logo = models.ImageField(upload_to=schools_determine_image_upload_path,
        null=True, storage=storage.ImageStorage(), blank=True)

    headers_color = models.CharField(max_length=7, default='#5a6579')
    headers_color_light = models.CharField(max_length=7, default='#f08c00')
    background_color = models.CharField(max_length=7, default='#ffffff')
    menu_color = models.CharField(max_length=7, default='#36cdc4')
    menu_color_light = models.CharField(max_length=7, default='#4bd2c9')

    sidebar_width = models.CharField(max_length=5, default='245px')
    show_school_organizers = models.BooleanField(default=True)

    extra_styles = models.TextField(blank=True)

    # The term names are used to import school courses from the old site.
    OLD_TERM_NAME_CHOICES = YEAR_IN_SCHOOL_CHOICES = (
        ('Math Future', 'School of the Mathematical Future'),
        ('SoSI', 'School of Social Innovation'),
        ('Webcraft', 'School of Webcraft'),
    )
    old_term_name = models.CharField(max_length=15, blank=True,
        null=True, choices=OLD_TERM_NAME_CHOICES)

    mentor_form_url = models.URLField(blank=True, null=True)
    mentee_form_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('school_home', (), {
            'slug': self.slug,
        })

    def save(self):
        """Make sure each school has a unique slug."""
        count = 1
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug
            while True:
                existing = School.objects.filter(slug=self.slug)
                if len(existing) == 0:
                    break
                self.slug = "%s-%s" % (slug, count + 1)
                count += 1
        super(School, self).save()


def projectsets_determine_image_upload_path(instance, filename):
    return "images/projectsets/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk),
        'filename': safe_filename(filename),
    }


class ProjectSet(ModelBase):
    "Model for the project sets"
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = RichTextField(config_name='rich')
    short_description = models.CharField(max_length=150)
    school = models.ForeignKey(School, blank=True, null=True,
        related_name="project_sets")
    projects = models.ManyToManyField('projects.Project', blank=True, null=True,
        related_name="projectsets", through='schools.ProjectSetIndex')
    featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to=projectsets_determine_image_upload_path,
        null=True, storage=storage.ImageStorage(), blank=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('school_projectset', (), {
            'slug': self.school.slug,
            'set_slug': self.slug,
        })

    def get_image_url(self):
        # TODO: using project's default image until a default badge
        # image is added.
        missing = settings.STATIC_URL + 'images/missing-challenge-set.png'
        image_path = self.image.url if self.image else missing
        return image_path

    def get_projects(self):
        return self.projects.order_by('projectsetindex__index')

    @property
    def first_project(self):
        try:
            return self.projects.order_by('projectsetindex__index')[0]
        except IndexError:
            return None

    def _distinct_participants(self):
        return UserProfile.objects.filter(participations__project__projectsets=self,
                                    deleted=False,
                                    participations__left_on__isnull=True).distinct()

    def total_participants(self):
        return self._distinct_participants().filter(
            participations__adopter = False,
            participations__organizing = False).count()
        
    def total_adopters(self):
        return self._distinct_participants().filter(
            Q(participations__adopter=True)
            | Q(participations__organizing=True)).count()

    def total_badges(self):
        return Badge.objects.filter(
            groups__projectsets=self).distinct().count()


class ProjectSetIndex(ModelBase):
    """Stores order of projects inside set"""
    projectset = models.ForeignKey('schools.ProjectSet')
    project = models.ForeignKey('projects.Project')
    index = models.IntegerField()
