from django.test import Client
from django.contrib.auth.models import User
from users.models import create_profile

from test_utils import TestCase

from courses import models as course_model
from content2 import models as content_model
from mock import patch


class CourseTests(TestCase):

    test_username = 'testuser'
    test_email = 'test@mail.org'
    test_password = 'testpass'

    test_username2 = 'bob'
    test_email2 = 'bob@mail.org'
    test_password2 = '13245'

    test_title = "A test course"
    test_hashtag = "hashtag"
    test_description = "This is only a test."

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


        self.course = course_model.create_course(
            **{
                "title": self.test_title,
                "hashtag": self.test_hashtag,
                "description": self.test_description,
                "language": "en",
                "organizer_uri": '/uri/users/testuser',
            }
        )
        content_model.update_content(
            self.course['about_uri'],
            'About',
            'This is the about content',
            '/uri/users/testuser'
        )
        
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
        self.assertTrue('slug' in course)
        self.assertTrue('description' in course)
        self.assertTrue('language' in course)
        self.assertTrue('date_created' in course)
        self.assertTrue('author_uri' in course)
        self.assertTrue('status' in course)
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

    def test_send_course_announcement(self):
        course = course_model.create_course(
            **{
                "title": "A test course",
                "hashtag": "ATC-1",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/testuser/'
            }
        )
        with patch('notifications.models.send_notifications_i18n') as send_notification:
            course_model.send_course_announcement(course['uri'], 'Notification text')
            self.assertTrue(send_notification.called)
            #TODO test parameters sent to send_notification


    def test_clone_course(self):
        clone = course_model.clone_course(self.course['uri'], '/uri/user/bob/')
        for key in ['title', 'hashtag', 'description', 'language']:
            self.assertEqual(clone[key], self.course[key])
        self.assertIn('based_on_uri', clone)

        about = content_model.get_content(self.course['about_uri'])
        clone_about = content_model.get_content(clone['about_uri'])
        self.assertEquals(about['content'], clone_about['content'])

        self.assertEqual(len(clone['content']), len(self.course['content']))
        for i in range(len(clone['content'])):
            self.assertEqual(clone['content'][i]['title'], self.course['content'][i]['title'])
            self.assertEqual(clone['content'][i]['content'], self.course['content'][i]['content'])

    def test_delete_spam_course(self):
        course = course_model.create_course(
            **{
                "title": "A test course",
                "hashtag": "ATC-1",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/testuser'
            }
        )
        course_model.delete_spam_course(course['uri'])
        with self.assertRaises(course_model.ResourceDeletedException):
            course_model.get_course(course['uri'])

    def test_get_courses(self):
        user = User(username='testuser99', email='99@example.com')
        user = create_profile(user)
        user.save()

        course = course_model.create_course(
            **{
                "title": "A test course",
                "hashtag": "ATC-1",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/testuser'
            }
        )
        
        course = course_model.create_course(
            **{
                "title": "A unique test course",
                "hashtag": "AUTC-1",
                "description": "This course is all about ABC",
                "language": "en",
                "organizer_uri": '/uri/user/testuser99'
            }
        )


        # get course by title
        courses = course_model.get_courses(title="A unique test course")
        self.assertEquals(len(courses), 1)

        # get course by user uri
        courses = course_model.get_courses(organizer_uri="/uri/user/testuser99")
        self.assertEquals(len(courses), 1)
