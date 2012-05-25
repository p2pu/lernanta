import logging
import os

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse


log = logging.getLogger(__name__)


BADGES_DB = 'badges_db'

RUBY = 6
EMERALD = 5
SAPPHIRE = 4

BADGES_MISSING_IMAGES = {
    RUBY: settings.STATIC_URL + 'images/ruby-missing.png',
    EMERALD: settings.STATIC_URL + 'images/emerald-missing.png',
    SAPPHIRE: settings.STATIC_URL + 'images/sapphire-missing.png',
}


def pilot_image(tag, badge):
    image_path = os.path.join(settings.BADGE_IMAGES_DIR,
        '%s.png' % tag.name)
    if os.path.exists(image_path):
        return '%s%s%s.png' % (settings.MEDIA_URL,
            settings.BADGE_IMAGES_URL, tag.name)
    else:
        return BADGES_MISSING_IMAGES[badge.type]


def get_badge_url(tag_name):
    url = None
    if not BADGES_DB in settings.DATABASES:
        return url
    try:
        tag = ForumTag.objects.using(BADGES_DB).get(
            name=tag_name)
        custom_badge = ForumCustombadge.objects.using(BADGES_DB).get(
            tag_id=tag.id)
        url = settings.BADGE_URL % dict(badge_id=custom_badge.ondb_id,
            badge_tag=tag.name)
    except (ForumTag.DoesNotExist, ForumCustombadge.DoesNotExist):
        pass
    return url


def get_awarded_badges(username):
    badges = {}
    if not BADGES_DB in settings.DATABASES:
        return badges
    try:
        user = User.objects.using(BADGES_DB).get(username=username)
        awards = ForumAward.objects.using(BADGES_DB).filter(user_id=user.id)
        for award in awards:
            badge = ForumBadge.objects.using(BADGES_DB).get(id=award.badge_id)
            if badge.type in [SAPPHIRE, EMERALD, RUBY]:
                custom_badge = ForumCustombadge.objects.using(BADGES_DB).get(
                    ondb_id=badge.id)
                tag = ForumTag.objects.using(BADGES_DB).get(
                    id=custom_badge.tag_id)
                if tag.name in badges:
                    badges[tag.name]['count'] += 1
                else:
                    url = settings.BADGE_EVIDENCE_URL % dict(badge_id=badge.id,
                        badge_tag=tag.name, username=username)
                    image_url = pilot_image(tag, badge)
                    description_url = reverse('badges_show',
                         kwargs=dict(slug=tag.name))
                    data = {
                        'name': custom_badge.name,
                        'type': badge.type,
                        'id': badge.id,
                        'evidence': url,
                        'image': image_url,
                        'count': 1,
                        'description': custom_badge.description,
                        'criteria': description_url,
                    }
                    badges[tag.name] = data
    except User.DoesNotExist:
        pass
    return badges


class ForumAward(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    badge_id = models.IntegerField()
    node_id = models.IntegerField(null=True, blank=True)
    awarded_at = models.DateTimeField()
    trigger_id = models.IntegerField(null=True, blank=True)
    action_id = models.IntegerField(unique=True)

    class Meta:
        db_table = u'forum_award'


class ForumBadge(models.Model):
    id = models.IntegerField(primary_key=True)
    type = models.IntegerField()
    cls = models.CharField(max_length=150, blank=True)
    awarded_count = models.IntegerField()

    class Meta:
        db_table = u'forum_badge'


class ForumCustombadge(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=300)
    description = models.CharField(max_length=300)
    long_description = models.TextField(blank=True)
    tag_id = models.IntegerField()
    ondb_id = models.IntegerField()
    is_peer_given = models.IntegerField()
    min_required_votes = models.IntegerField()
    voting_restricted = models.IntegerField()

    class Meta:
        db_table = u'forum_custombadge'


class ForumTag(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=765)
    created_by_id = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField()

    class Meta:
        db_table = u'forum_tag'
