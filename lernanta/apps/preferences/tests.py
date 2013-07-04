from django.core import mail
from django.contrib.auth.models import User

from test_utils import TestCase

from relationships.models import Relationship
from users.models import UserProfile, create_profile
from preferences.models import get_notification_subscription
from preferences.models import set_notification_subscription


class AccountPreferencesTests(TestCase):

    test_users = [
        dict(username='test_one', email='test_one@mozillafoundation.org'),
        dict(username='test_two', email='test_two@mozillafoundation.org'),
    ]

    def setUp(self):
        """Create data for testing."""
        for user in self.test_users:
            django_user = User(**user)
            user = create_profile(django_user)
            user.set_password('testpass')
            user.save()
        (self.user_one, self.user_two) = UserProfile.objects.all()


    def test_new_follower_email_preference(self):
        """
        Test user is emailed when they get a new follower when that
        user wants to be emailed when they get a new follower.
        """
        relationship = Relationship(
            source=self.user_one,
            target_user=self.user_two,
        )
        relationship.save()
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [self.user_two.email, ])

    def test_no_new_follower_email_preference(self):
        """
        Test user is *not* emailed when they get a new follower when that user
        does *not* want to be emailed when they get a new follower.
        """
        set_notification_subscription(self.user_two, 'new-follower', False)

        relationship = Relationship(
            source=self.user_one,
            target_user=self.user_two,
        )
        relationship.save()
        self.assertEquals(len(mail.outbox), 0)


    def test_notification_subscription(self):
        """ Test if notification subscriptions work """
        res = get_notification_subscription(self.user_one, '')
        self.assertFalse(res)

        res = get_notification_subscription(self.user_one, 'course-announcement.course-1')
        self.assertTrue(res)

        with self.assertRaises(Exception):
            res = get_notification_subscription(self.user_one, 'whatever')
        
        set_notification_subscription(self.user_one, 'course-announcement.course-1', False)
        res = get_notification_subscription(self.user_one, 'course-announcement.course-1')
        self.assertFalse(res)

        res = get_notification_subscription(self.user_one, 'course-announcement.course-2')
        self.assertTrue(res)

        set_notification_subscription(self.user_one, 'course-announcement', False)
        res = get_notification_subscription(self.user_one, 'course-announcement.course-2')
        self.assertFalse(res)
        
        set_notification_subscription(self.user_one, 'course-announcement', True)
        res = get_notification_subscription(self.user_one, 'course-announcement.course-2')
        self.assertTrue(res)
        
        set_notification_subscription(self.user_one, 'course-announcement.course-1', True)
        res = get_notification_subscription(self.user_one, 'course-announcement.course-1')
        self.assertTrue(res)
        
        set_notification_subscription(self.user_one, 'course-3', False)
        res = get_notification_subscription(self.user_one, 'course-signup.course-3')
        self.assertFalse(res)
        
        set_notification_subscription(self.user_one, 'course-3', False)
        res = get_notification_subscription(self.user_one, 'course-signup.course-3')
        self.assertFalse(res)
