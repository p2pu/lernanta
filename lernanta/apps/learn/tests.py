from django.test import Client
from django.contrib.auth.models import User

from users.models import create_profile
from projects.models import Project
from learn.models import get_listed_courses

from test_utils import TestCase


class ProjectTests(TestCase):

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

    def test_get_listed_courses(self):
        deleted_project = Project(deleted=True, test=False)
        deleted_project.save()
       
        not_listed_project = Project(not_listed=True, test=False)
        not_listed_project.save()
       
        under_dev_project = Project(name="under_dev:default", test=False)
        under_dev_project.save()

        archived_project = Project(under_development=False, archived=True)
        archived_project.save()

        test_project = Project(under_development=False, test=True)
        test_project.save()

        project = Project(name="listed", under_development=False, test=False)
        project.save()
       
        listed_projects = get_listed_courses()

        self.assertFalse(deleted_project in listed_projects)
        self.assertFalse(not_listed_project in listed_projects)
        self.assertFalse(under_dev_project in listed_projects)
        self.assertFalse(test_project in listed_projects)
 
