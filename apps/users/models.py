import logging
import datetime
import bleach
import random
import string
import hashlib
import os


from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.utils.http import urlquote_plus
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.safestring import mark_safe

from taggit.models import GenericTaggedItemBase, Tag
from taggit.managers import TaggableManager

from drumbeat import storage
from drumbeat.utils import get_partition_id, safe_filename
from drumbeat.models import ModelBase
from relationships.models import Relationship
from projects.models import Project
from users import tasks 

import caching.base

log = logging.getLogger(__name__)

GRAVATAR_TEMPLATE = ("http://www.gravatar.com/avatar/%(gravatar_hash)s"
                     "?s=%(size)s&amp;d=%(default)s&amp;r=%(rating)s")

def determine_upload_path(instance, filename):
    chunk_size = 1000  # max files per directory
    return "images/profiles/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk, chunk_size),
        'filename': safe_filename(filename),
    }


def get_hexdigest(algorithm, salt, raw_password):
    """Generate password hash."""
    return hashlib.new(algorithm, smart_str(salt + raw_password)).hexdigest()


def create_password(algorithm, raw_password):
    """Create salted, hashed password."""
    salt = os.urandom(5).encode('hex')
    hsh = get_hexdigest(algorithm, salt, raw_password)
    return '$'.join((algorithm, salt, hsh))


class ProfileTag(Tag):
    CATEGORY_CHOICES = (
        ('skill', 'Skill'),
        ('interest', 'Interest'),
    )
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)


class TaggedProfile(GenericTaggedItemBase):
    tag = models.ForeignKey(
        ProfileTag, related_name="%(app_label)s_%(class)s_items")

    class Meta:
        verbose_name = "Tagged User Profile"
        verbose_name_plural = "Tagged User Profiles"


class UserProfileManager(caching.base.CachingManager):

    def get_popular(self, limit=0):
        users = Relationship.objects.values('target_user_id').annotate(
            models.Count('id')).filter(target_user__featured=False).order_by(
            '-id__count')[:limit]
        user_ids = [u['target_user_id'] for u in users]
        return UserProfile.objects.filter(id__in=user_ids)


class UserProfile(ModelBase):
    """Each user gets a profile."""
    object_type = 'http://activitystrea.ms/schema/1.0/person'

    username = models.CharField(max_length=255, default='', unique=True)
    full_name = models.CharField(
        max_length=255, default='', null=True, blank=True)
    password = models.CharField(max_length=255, default='')
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(blank=True, default='')
    image = models.ImageField(
        upload_to=determine_upload_path, default='', blank=True, null=True,
        storage=storage.ImageStorage())
    confirmation_code = models.CharField(
        max_length=255, default='', blank=True)
    location = models.CharField(max_length=255, blank=True, default='')
    featured = models.BooleanField()
    newsletter = models.BooleanField()
    discard_welcome = models.BooleanField(default=False)
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
    preflang = models.CharField(verbose_name = 'preferred language',
        max_length = 16, choices = settings.SUPPORTED_LANGUAGES,
        default = settings.LANGUAGE_CODE)

    user = models.ForeignKey(User, null=True, editable=False, blank=True)
    tags = TaggableManager(through=TaggedProfile)

    objects = UserProfileManager()

    def __unicode__(self):
        return self.full_name or self.username

    def following(self, model=None):
        """
        Return a list of objects this user is following. All objects returned
        will be ```Project``` or ```UserProfile``` instances. Optionally filter
        by type by including a ```model``` parameter.
        """
        if (model == 'Project' or isinstance(model, Project) or
            model == Project):
            relationships = Relationship.objects.select_related(
                'target_project').filter(source=self).exclude(
                target_project__isnull=True)
            return [rel.target_project for rel in relationships]
        relationships = Relationship.objects.select_related(
            'target_user').filter(source=self).exclude(
            target_user__isnull=True)
        return [rel.target_user for rel in relationships]

    def followers(self):
        """Return a list of this users followers."""
        relationships = Relationship.objects.select_related(
            'source').filter(target_user=self)
        return [rel.source for rel in relationships]

    def is_following(self, model):
        """Determine whether this user is following ```model```."""
        return model in self.following(model=model)

    @models.permalink
    def get_absolute_url(self):
        return ('users_profile_view', (), {
            'username': self.username,
        })

    def email_confirmation_code(self, url):
        """Send a confirmation email to the user after registering."""
        body = render_to_string('users/emails/registration_confirm.txt', {
            'confirmation_url': url,
        })
        subject = ugettext('Complete Registration')
        # During registration use the interface language to send email
        tasks.SendUserEmail.apply_async(args=(self, subject, body))

    def image_or_default(self):
        """Return user profile image or a default."""
        gravatarUrl = self.gravatar(54) 
        avatar = '%s%s' % (settings.MEDIA_URL, '/images/member-missing.png')
        if self.image:
        	avatar =  '%s%s' % (settings.MEDIA_URL, self.image)
        elif gravatarUrl:
        	avatar = gravatarUrl
        return mark_safe(avatar)

    def gravatar(self, size=54):
        hash = hashlib.md5(self.email.lower()).hexdigest() 
        default = urlquote_plus(settings.DEFAULT_PROFILE_IMAGE)
        return GRAVATAR_TEMPLATE % {
            'size': size,
            'gravatar_hash': hash,
            'default': default,
            'rating': "g",
            'username': self.username,
            } 
    
    def generate_confirmation_code(self):
        if not self.confirmation_code:
            self.confirmation_code = ''.join(random.sample(string.letters +
                                                           string.digits, 60))
        return self.confirmation_code

    def set_password(self, raw_password, algorithm='sha512'):
        self.password = create_password(algorithm, raw_password)

    def check_password(self, raw_password):
        if '$' not in self.password:
            valid = (get_hexdigest('md5', '', raw_password) == self.password)
            if valid:
                # Upgrade an old password.
                self.set_password(raw_password)
                self.save()
            return valid

        algo, salt, hsh = self.password.split('$')
        return hsh == get_hexdigest(algo, salt, raw_password)

    @property
    def display_name(self):
        return self.full_name or self.username


def create_profile(user, username=None):
    """Make a UserProfile for this django.contrib.auth.models.User."""
    if UserProfile.objects.all().count() == 0:
        user.is_superuser = True
        user.is_staff = True
    user.save()
    profile = UserProfile(id=user.id)
    profile.user = user
    profile.user_id = user.id
    if username:
        profile.username = username
    else:
        profile.username = user.username
    profile.email = user.email
    profile.save()
    return profile

        
###########
# Signals #
###########

def clean_html(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if isinstance(instance, UserProfile): 
        if instance.bio:
            instance.bio = bleach.clean(instance.bio,
                tags=settings.REDUCED_ALLOWED_TAGS, attributes=settings.REDUCED_ALLOWED_ATTRIBUTES,
                strip=True)

pre_save.connect(clean_html, sender=UserProfile)
