import logging

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

BADGES_DB = 'badges_db'

RUBY = 6
EMERALD = 5
SAPPHIRE = 4

BADGES_MISSING_IMAGES = {
    RUBY: settings.MEDIA_URL + 'images/ruby-missing.png',
    EMERALD: settings.MEDIA_URL + 'images/emerald-missing.png',
    SAPPHIRE: settings.MEDIA_URL + 'images/sapphire-missing.png',
}


log = logging.getLogger(__name__)


def get_awarded_badges(username):
    if not BADGES_DB in settings.DATABASES:
        return []
    badges = {}
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
                    url = settings.BADGE_URL % dict(badge_id=badge.id,
                        badge_tag=tag.name, username=username)
                    image_url = BADGES_MISSING_IMAGES[badge.type]
                    data = {
                        'name': custom_badge.name,
                        'type': badge.type,
                        'id': badge.id,
                        'url': url,
                        'image_url': image_url,
                        'count': 1,
                        'description': 'some description necessary',
                        'template': re.sub(r'\?.*', '', url),
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
