from django.test import Client
from django.contrib.auth.models import User

from users.models import create_profile
from schools.models import School

from test_utils import TestCase


class SchoolTests(TestCase):

    test_username = 'testuser'
    test_email = 'test@mozillafoundation.org'
    test_password = 'testpass'

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

    def test_create_school(self):
        school = School(
            name = "The great School of Test",
            short_name = "test school",
            description = "<p>Some rich text description?</p>"
        )
        school.save()
        self.assertEqual('the-great-school-of-test', school.slug)

        self.assertEqual(
            School.objects.get(slug='the-great-school-of-test'),
            school
        )
        
