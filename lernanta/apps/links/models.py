import logging

from django.db import models
# from django.db.models.signals import post_save, post_delete

from django_push.subscriber.models import Subscription
# from django_push.subscriber.signals import updated
from django.db.models import Max
from links.tasks import SubscribeToFeed, UnsubscribeFromFeed, HandleNotification


log = logging.getLogger(__name__)


class Link(models.Model):
    """
    A link that can be added to a project or user. Links that have an Atom or
    RSS feed will be subscribed to using the declared hub or SuperFeedrs.
    """
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=1023)
    project = models.ForeignKey('projects.Project', null=True)
    user = models.ForeignKey('users.UserProfile', null=True)
    subscribe = models.BooleanField(default=False)
    subscription = models.ForeignKey(Subscription, null=True)
    index = models.IntegerField(null=True, default=0, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.index:
            if self.project:
                max_index = Link.objects.filter(
                    project=self.project).aggregate(Max('index'))['index__max']
            else:
                max_index = Link.objects.filter(user=self.user,
                    project__isnull=True).aggregate(Max('index'))['index__max']
            self.index = max_index + 1 if max_index else 1
        super(Link, self).save(*args, **kwargs)


def link_create_handler(sender, **kwargs):
    """Check for a feed and subscribe to it if it exists."""
    link = kwargs.get('instance', None)
    if not isinstance(link, Link):
        return
    if link.subscribe:
        SubscribeToFeed.apply_async(args=(link,))

# post_save.connect(link_create_handler, sender=Link,
#     dispatch_uid='links_link_create_handler')


def link_delete_handler(sender, **kwargs):
    """If the link had an associated feed subscription, unsubscribe."""
    link = kwargs.get('instance', None)

    if not isinstance(link, Link):
        return

    try:
        if not link.subscription:
            return
    except Subscription.DoesNotExist:
        return

    UnsubscribeFromFeed.apply_async(args=(link,))

# post_delete.connect(link_delete_handler, sender=Link,
#     dispatch_uid='links_link_delete_handler')


def listener(notification, **kwargs):
    """
    Create activity entries when we receive notifications of
    feed updates from a hub.
    """
    sender = kwargs.get('sender', None)
    if not sender:
        return
    try:
        msg = 'Received feed update notification: %s, sender: %s'
        log.debug(msg % (notification, sender))
        eager_result = HandleNotification.apply_async(
            args=(notification, sender))
        msg = 'Result from the feed notification handler: %s, %s'
        log.debug(msg % (eager_result.status, eager_result.result))
    except Exception, ex:
        log.warn("Unprocessable notification: %s (%s)" % (notification, ex))
#updated.connect(listener, dispatch_uid='links_listener')
