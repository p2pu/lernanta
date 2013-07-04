from django.db import models
from django.utils.translation import ugettext_lazy as _

from drumbeat.models import ModelBase


class AccountPreferences(ModelBase):
    preferences = (
        'no_email_message_received',
        'no_email_new_follower',
        'no_email_new_project_follower',
        'no_email_new_badge_submission',
    )
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=100)
    user = models.ForeignKey('users.UserProfile')


NOTIFICATION_CATEGORIES = [
    {'category': 'account', 'description': _('Account management notifications') },
    {'category': 'abuse-report', 'description': _('Abuse report') },
    {'category': 'course-created', 'description': _('Course created') },
    {'category': 'direct-message', 'description': _('Direct message') },
    {'category': 'status-update', 'description': _('Status update posted') }, #TODO we don't really support this anymore!
    {'category': 'new-follower', 'description': _('New follower') },

    {'category': 'course-signup', 'description': _('New course signup') },
    {'category': 'course-review', 'description': _('New course review') },
    {'category': 'course-announcement', 'description': _('Course announcements') },
    {'category': 'signup-answer', 'description': _('Course signup answer') }, #TODO deprecated
    {'category': 'content-updated', 'description': _('Content updated') },

    
    {'category': 'badges', 'description': _('Notification from badges.p2pu.org') },
    {'category': 'badge-submission', 'description': _('Application for a badge submitted')},
    {'category': 'badge-review', 'description': _('Feedback on badge application') },
    
    {'category': 'reply', 'description': _('Reply to comment or status update') },
]


class NotificationSubscription(ModelBase):
    user = models.ForeignKey('users.UserProfile')
    category = models.CharField(max_length=128, blank=True, null=True)
    subcategory = models.CharField(max_length=128, blank=True, null=True)


"""
Notification categories are dot delimited keys. The part before the dot is the
general category and the part after the dot is the specific category.
Ex. signup, message, follow, signup.course-1, announcement.course-1

Users can unsubscribe from a specific category: signup.course-1 or the more
general categories: signup or course-1.

A user unsubscribed from signup.course-1 will receive notifications for signup
A user unsubscribed from signup will not receive notification for signup.course-1
A user unsubscribed from course-1 will not receive notificatinos for announce.course-1
A user unsubscribed from course-1.signup is incorrect!
"""

def get_notification_categories():
    return NOTIFICATION_CATEGORIES
    return [category.category for category in NotificationCategory.objects.all()]


def get_notification_subscription(profile, notification_category):
    """ check if a user is subscribed to a notification category """
    
    categories = notification_category.split('.')

    if len(notification_category) == 0:
        return False

    category = categories[0]

    if not category in [c['category'] for c in NOTIFICATION_CATEGORIES]:
        raise Exception('Unknown category')

    # check if user unsubscribed from the general category
    subscriptions = NotificationSubscription.objects.filter(
        category=category, user=profile, subcategory__isnull=True
    )
    if subscriptions.exists():
        return False

    if len(categories) == 2:
        # check if user unsubscribed from the specific category
        subscriptions = NotificationSubscription.objects.filter(
            category=category, user=profile, subcategory=categories[1]
        )
        if subscriptions.exists():
            return False

        # check if user is unsubscribed from the subcategory
        subscriptions = NotificationSubscription.objects.filter(
            category=None, user=profile, subcategory=categories[1]
        )
        if subscriptions.exists():
            return False

    return True


def set_notification_subscription(profile, notification_category, subscribed):
    
    if len(notification_category) == 0:
        raise Exception('Cannot unsubscribe from a blank category')

    categories = notification_category.split('.')

    category = None
    subcategory = None
    if len(categories) == 1:
        if categories[0] in [c['category'] for c in NOTIFICATION_CATEGORIES]:
            category = categories[0]
        else:
            subcategory = categories[0]
    else:
        category = categories[0]
        subcategory = categories[1]
        
    subscription = NotificationSubscription.objects.filter(
        user=profile,
        category=category,
        subcategory=subcategory
    )

    if subscription.exists() and subscribed:
        subscription.delete()

    elif not subscription.exists() and not subscribed and category != 'account':
        subscription = NotificationSubscription(
            user=profile,
            category=category,
            subcategory=subcategory
        )
        subscription.save()


def get_user_unsubscribes(profile):
    """ get all the unsubscribes for a user """
    unsubscribes = []
    for subscription in NotificationSubscription.objects.filter(user=profile):
        if subscription.category and subscription.subcategory:
            unsubscribes.append('.'.join([subscription.category, subscription.subcategory]))
        elif subscription.category:
            unsubscribes.append(subscription.category)
        elif subscription.subcategory:
            unsubscribes.append(subscription.subcategory)
    return unsubscribes
