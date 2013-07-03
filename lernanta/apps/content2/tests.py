from django.test import Client
from django.contrib.auth.models import User
from users.models import create_profile

from test_utils import TestCase

from content2 import models as content_model
from mock import patch


class CourseTests(TestCase):

    test_username = 'testuser'
    test_email = 'test@mail.org'
    test_password = 'testpass'

    test_username2 = 'bob'
    test_email2 = 'bob@mail.org'
    test_password2 = '13245'

    def setUp(self):
        self.client = Client()
        self.locale = 'en'

        django_user = User(
            username=self.test_username,
            email=self.test_email,
        )
        self.user = create_profile(django_user)
        self.user.set_password(self.test_password)
        self.user.save()
        
        django_user2 = User(
            username=self.test_username2,
            email=self.test_email2,
        )
        self.user2 = create_profile(django_user2)
        self.user2.set_password(self.test_password2)
        self.user2.save()


    def test_content_creation(self):
        content = content_model.create_content('title', 'content', '/uri/users/bob')
        content2 = content_model.get_content(content['uri'])
        self.assertEquals(content, content2)


    def test_content_history(self):
        content = content_model.create_content('title', 'content', '/uri/users/bob')
        content_model.update_content(
            content['uri'], 'New title', 'New content', '/uri/users/testuser'
        )


    def test_clone_content(self):
        content = content_model.create_content('title', 'content', '/uri/users/bob')
        clone = content_model.clone_content(content['uri'])
        for key in ['title', 'content']:
            self.assertTrue(content[key], clone[key])
