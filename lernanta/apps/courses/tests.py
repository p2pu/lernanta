from django.test import Client
from django.contrib.auth.models import User

from test_utils import TestCase

from courses import models as course_model
from content2 import models as content_model


class CourseTests(TestCase):

    test_username = 'testuser'
    test_email = 'test@mozillafoundation.org'
    test_password = 'testpass'

    test_title = "A test course"
    test_hashtag = "hashtag"
    test_description = "This is only a test."

    def setUp(self):
        self.client = Client()
        self.locale = 'en'
        self.course = course_model.create_course(
            **{
                "title": self.test_title,
                "hashtag": self.test_hashtag,
                "description": self.test_description,
                "language": "en",
                "organizer_uri": '/uri/users/testuser',
            }
        )
        #django_user = User(
        #    username=self.test_username,
        #    email=self.test_email,
        #)
        #self.user = create_profile(django_user)
        #self.user.set_password(self.test_password)
        #self.user.save()

    def test_course_creation(self):
        course = course_model.create_course(
            **{
                "title": "A test course",
                "hashtag": "ATC-1",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/testuser'
            }
        )

        self.assertTrue(not course == None)

        # test that about content was created
        about = content_model.get_content(course['about_uri'])
        self.assertTrue(not about == None)
        self.assertEqual(about['title'], "About")

        # test that a cohort was created
        cohort = course_model.get_course_cohort(course['uri'])
        self.assertTrue(not cohort == None)

        self.assertTrue(
            course_model.user_in_cohort('/uri/user/testuser', cohort['uri'])
        )
        self.assertTrue(
            course_model.is_cohort_organizer('/uri/user/testuser', cohort['uri'])
        )

    def test_course_get(self):
        course = course_model.get_course(self.course['uri'])
        self.assertTrue('id' in course)
        self.assertTrue('uri' in course)
        self.assertTrue('title' in course)
        self.assertTrue('hashtag' in course)
        self.assertTrue('about_uri' in course)
        self.assertTrue('slug' in course)
        self.assertTrue('description' in course)
        self.assertTrue('language' in course)
        self.assertTrue('draft' in course)
        self.assertTrue('archived' in course)
        self.assertTrue('about_uri' in course)
        self.assertTrue('content' in course)

    def test_add_content(self):
        pass

    def test_add_user(self):
        cohort = course_model.get_course_cohort(self.course['uri'])
        course_model.add_user_to_cohort(
            cohort['uri'], '/uri/user/bob', 'ORGANIZER')
        cohort2 = course_model.get_course_cohort(self.course['uri'])
        self.assertEqual(len(cohort['users']), len(cohort2['users'])-1)

    def test_remove_user(self):
        pass

    def test_make_organizer(self):
        pass
