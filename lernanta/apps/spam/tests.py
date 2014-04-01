from django.contrib.auth.models import User
from users.models import create_profile

from test_utils import TestCase

from courses import models as course_model
from spam import models as spam_model
from mock import patch


class SpamTests(TestCase):

    test_username = 'spammer'
    test_email = 'test@mail.org'
    test_password = 'testpass'

    test_title = "Spam course"
    test_hashtag = "hashtag"
    test_description = "This is only a test."


    def setUp(self):
        self.locale = 'en'

        django_user = User(
            username=self.test_username,
            email=self.test_email,
        )
        self.user = create_profile(django_user)
        self.user.set_password(self.test_password)
        self.user.save()
        
        
    def test_spam_course_deletion(self):
        course = course_model.create_course(
            **{
                "title": "A spam course",
                "hashtag": "ASC",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/spammer'
            }
        )

        self.assertEqual(course_model.get_course(course['uri']), course)

        spam_model.handle_spam_user('spammer')
        with self.assertRaises(course_model.ResourceDeletedException):
            course_model.get_course(course['uri'])

