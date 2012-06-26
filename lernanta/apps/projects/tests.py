from django.test import Client
from django.contrib.auth.models import User

from users.models import create_profile
from projects.models import Project

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

    def test_unique_slugs(self):
        """Test that each project will get a unique slug"""
        project = Project(
            name='My Cool Project',
            short_description='This project is awesome',
            long_description='No really, its good',
        )
        project.save()
        self.assertEqual('my-cool-project', project.slug)
        project2 = Project(
            name='My Cool  Project',
            short_description='This project is awesome',
            long_description='This is all very familiar',
        )
        project2.save()
        self.assertEqual('my-cool-project-2', project2.slug)

    def test_course_creation(self):
        """Test valid post request to course creation page"""
        data = {
            'name': 'Test New Course',
            'short_description': 'This is my new course',
            'long_description': '<p>The new course is about...</p>',
            'language': 'en',
            'category': 'course',
        }
        self.client.login(username=self.test_username,
            password=self.test_password)
        response = self.client.post('/%s/groups/create/' % (self.locale,),
            data)
        self.assertRedirects(response,
            '/%s/groups/%s/create/tasks/' % (self.locale, 'test-new-course'),
            target_status_code=200)

    def test_challenge_creation(self):
        """Test valid post request to challenge creation page"""
        data = {
            'name': 'Test New Challenge',
            'short_description': 'This is my new challenge',
            'long_description': '<p>The new challenge is about...</p>',
            'language': 'en',
            'category': 'challenge',
            'duration': 10,
        }
        self.client.login(username=self.test_username,
            password=self.test_password)
        response = self.client.post('/%s/groups/create/' % (self.locale,),
            data)
        slug = 'test-new-challenge'
        self.assertRedirects(response,
            '/%s/groups/%s/create/tasks/' % (self.locale, slug),
            target_status_code=200)
        challenge = Project.objects.get(slug=slug)
        self.assertEqual(challenge.category, Project.CHALLENGE)
        self.assertEqual(challenge.duration_hours, 10)

    def test_get_listed_projects(self):
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
       
        listed_projects = Project.get_listed_projects()

        self.assertFalse(deleted_project in listed_projects)
        self.assertFalse(not_listed_project in listed_projects)
        self.assertFalse(under_dev_project in listed_projects)
        self.assertFalse(test_project in listed_projects)
        self.assertTrue(project in listed_projects)
