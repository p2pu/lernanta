from django.conf import settings
from django.test import Client

from django.contrib.auth.models import User

from django.utils.translation import activate
from users.models import create_profile

from test_utils import TestCase

class TestUserProfileRedirects(TestCase):
    """
    Test redirection for old-style user profile URLs:
      http://whatever/username => http://whatever/locale/people/username
    and:
      http://whatever/locale/username => http://whatever/locale/people/username
    * Redirecting from /something/username to /something/username/
      (with a trailing '/') is a 301, not a 302.
    * User profile URLs all have a trailing slash; if the test URL does not
      have this, we get a redirect, but if it does, we might get a 200 right
      away.
    * The url '/en/people' looks like an attempt to access the profile for
      a user named 'people', but since we have APPEND_SLASH=True in settings.py,
      the failure to find a page for '/en/people' is redirected to the page
      '/en/people/', which matches the general list page for people, before
      our middleware is called.
    """

    def setUp(self):
        self.username = 'luke'
        self.email = 'luke@example.com'
        self.client = Client()
        u = User(username=self.username, email=self.email)
        create_profile(u)

    def test_username_without_locale_in_url_when_locale_not_activated(self):
        original = '/%s' % self.username # no trailing '/'
        expected = '/en/people/%s/' % self.username
        response = self.client.get(original, follow=True)
        self.assertRedirects(response, expected, status_code=301, target_status_code=200)

    def test_username_without_locale_in_url_when_locale_activated(self):
        activate('en') # make sure we know what locale we're in
        original = '/%s' % self.username # no trailing '/'
        expected = '/en/people/%s/' % self.username
        response = self.client.get(original, follow=True)
        self.assertRedirects(response, expected, status_code=301, target_status_code=200)

    def test_username_with_locale_in_url_when_locale_not_activated(self):
        original = '/en/%s' % self.username
        expected = '/en/people/%s/' % self.username
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=302, target_status_code=200)

    def test_username_with_locale_in_url_when_locale_activated(self):
        activate('en') # make sure we know what locale we're in
        original = '/en/%s' % self.username
        expected = '/en/people/%s/' % self.username
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=302, target_status_code=200)

    def test_username_with_locale_and_people_in_url_when_locale_not_activated(self):
        original = '/en/people/%s/' % self.username # has trailing '/'
        expected = original
        response = self.client.get(original)
        self.assertEquals(200, response.status_code)

    def test_username_with_locale_and_people_in_url_when_locale_activated(self):
        activate('en') # make sure we know what locale we're in
        original = '/en/people/%s' % self.username # no trailing '/'
        expected = '/en/people/%s/' % self.username
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=301, target_status_code=200)

    def test_locale_and_username_with_different_valid_locale_when_no_locale_activated(self):
        """
        Need this test because the regular expression contains locale_1|locale_2|locale_3,
        and the ordering of fields might matter.
        """
        original = '/es/%s/' % self.username # not the same locale as other tests
        expected = '/es/people/%s/' % self.username # same locale as line above
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=302, target_status_code=200)
    
    def test_username_with_different_valid_locale_when_locale_activated(self):
        """
        See explanation above.
        """
        activate('en')
        original = '/es/%s' % self.username
        expected = '/es/people/%s/' % self.username
        response = self.client.get(original, follow=True)
        self.assertRedirects(response, expected, status_code=302, target_status_code=200)
    
    def test_username_with_invalid_locale(self):
        activate('en') # make sure we know what locale we're in
        original = '/invalid_locale/%s' % self.username
        expected = '/en/invalid_locale/%s' % self.username
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=301, target_status_code=404)

    def test_base_url_only(self):
        activate('en') # make sure we know what locale we're in
        original = '/people/'
        expected = '/en/people/'
        response = self.client.get(original)
        self.assertRedirects(response, expected, status_code=301, target_status_code=200)
