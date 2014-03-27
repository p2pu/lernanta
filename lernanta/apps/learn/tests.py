from django.test import Client
from django.contrib.auth.models import User

from users.models import create_profile
from learn.models import add_course_listing
from learn.models import update_course_listing
from learn.models import remove_course_listing
from learn.models import get_listed_courses
from learn.models import create_list
from learn.models import add_course_to_list
from learn.models import remove_course_from_list
from learn.models import get_courses_by_list
from learn.models import get_courses_by_tags
from learn.models import get_tags_for_courses
from learn.models import get_active_languages
from learn.models import get_courses_by_language
from learn.db import CourseTags

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

        self.test_course = {
            "course_url": "http://p2pu.org/courses/1/", 
            "title": "Course title", 
            "description": "Short description", 
            "data_url": "", 
            "language": "en", 
            "thumbnail_url": "http://p2pu.org/media/image.png", 
            "tags": ["tag1", "tag2", "tag3"]
        }


    def test_add_course_listing(self):
        """ test that courses are added to the course list """

        add_course_listing(**self.test_course)
        listed_courses = get_listed_courses()

        self.assertTrue(len(listed_courses) == 1)
        self.assertTrue(self.test_course['course_url'] == listed_courses[0].url)


    def test_update_course(self):
        """ test that course data gets updated """

        add_course_listing(**self.test_course)
        updated_course = {
            "title": 'New Title',
            "description": "New description",
            "data_url": "http://example.com", 
            "language": "es", 
            "thumbnail_url": "http://p2pu.org/media/new_image.png"
        }
        update_course_listing(self.test_course['course_url'] ,**updated_course)
        listed_courses = get_listed_courses()

        self.assertTrue(len(listed_courses) == 1)
        self.assertTrue(listed_courses[0].title == updated_course['title'])
        self.assertTrue(listed_courses[0].description == updated_course['description'])
        self.assertTrue(listed_courses[0].data_url == updated_course['data_url'])
        self.assertTrue(listed_courses[0].language == updated_course['language'])
        self.assertTrue(listed_courses[0].thumbnail_url == updated_course['thumbnail_url'])


    def test_remove_course(self):
        """ test that courses are removed from the course list """

        self.assertEquals(CourseTags.objects.count(), 0)
        add_course_listing(**self.test_course)
        self.assertEquals(CourseTags.objects.count(), 3)
        remove_course_listing(self.test_course['course_url'])
        listed_courses = get_listed_courses()

        self.assertEquals(len(listed_courses), 0)
        self.assertEquals(CourseTags.objects.count(), 0)
        # TODO test that course tags are also deleted


    def test_course_list(self):
        """ test that course can be added to and removed from a list """

        add_course_listing(**self.test_course)
        create_list("test_list", "Test List", "")
        add_course_to_list(self.test_course["course_url"], "test_list")
        course_list = get_courses_by_list("test_list")

        self.assertTrue(len(course_list) == 1)

        remove_course_from_list(self.test_course["course_url"], "test_list")
        course_list = get_courses_by_list("test_list")

        self.assertTrue(len(course_list) == 0)


    def test_course_tags(self):
        """ test that course tags works as expected """

        add_course_listing(**self.test_course)
        course_list = get_courses_by_tags(self.test_course["tags"])
        tags = get_tags_for_courses(course_list)

        self.assertTrue(len(course_list) == 1)
        self.assertTrue(course_list[0].url == self.test_course["course_url"])
        self.assertTrue(len(tags) == len(self.test_course["tags"]))


    def test_course_language(self):
        """ test that course languages are handled correctly """

        add_course_listing(**self.test_course)

        es_course = {
            "course_url": "http://p2pu.org/courses/2/", 
            "title": "Course title", 
            "description": "Short description", 
            "data_url": "", 
            "language": "es", 
            "thumbnail_url": "http://p2pu.org/media/image.png", 
            "tags": ["tag1", "tag2", "tag3"]
        }
        add_course_listing(**es_course)

        es_course['course_url'] = "http://p2pu.org/courses/3/"
        add_course_listing(**es_course)

        nl_course = {
            "course_url": "http://p2pu.org/courses/4/", 
            "title": "Course title", 
            "description": "Short description", 
            "data_url": "", 
            "language": "nl", 
            "thumbnail_url": "http://p2pu.org/media/image.png", 
            "tags": ["tag1", "tag2", "tag3"]
        }
        add_course_listing(**nl_course)

        course_list = get_listed_courses()
        self.assertTrue(len(course_list) == 4)
        
        languages = get_active_languages()
        self.assertTrue(len(languages) == 3)

        spanish_courses = get_courses_by_language("es")
        self.assertTrue(len(spanish_courses) == 2)

