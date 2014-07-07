from django.conf import settings
from django.test import Client
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User

from l10n.urlresolvers import reverse
from drumbeat.utils import get_partition_id
from users.models import create_profile

from test_utils import TestCase


class TestLogins(TestCase):

    test_username = 'testuser'
    test_password = 'testpassword'
    test_email = 'test@mozillafoundation.org'

    def setUp(self):
        self.locale = 'en'
        self.client = Client()
        django_user = User(username=self.test_username,
                           email=self.test_email)
        self.user = create_profile(django_user)
        self.user.set_password(self.test_password)
        self.user.save()
        self.old_recaptcha_pubkey = settings.RECAPTCHA_PUBLIC_KEY
        self.old_recaptcha_privkey = settings.RECAPTCHA_PRIVATE_KEY
        settings.RECAPTCHA_PUBLIC_KEY, settings.RECAPTCHA_PRIVATE_KEY = '', ''

    def tearDown(self):
        settings.RECAPTCHA_PUBLIC_KEY = self.old_recaptcha_pubkey
        settings.RECAPTCHA_PRIVATE_KEY = self.old_recaptcha_privkey

    def test_authenticated_redirects(self):
        """Test that authenticated users are redirected in specific views."""
        self.client.login(username=self.test_username,
                          password=self.test_password)
        paths = ('login/', 'register/')
        for path in paths:
            full = "/%s/%s" % (self.locale, path)
            response = self.client.get(full)
            self.assertRedirects(response, '/en/home/dashboard/', status_code=302,
                                 target_status_code=302)
        self.client.logout()

    def test_unauthenticated_redirects(self):
        """Test that anonymous users are redirected for specific views."""
        paths = ('logout/', 'profile/edit/', 'profile/edit/image/')
        for path in paths:
            full = "/%s/%s" % (self.locale, path)
            response = self.client.get(full)
            expected = "%s?next=/%s/%s" % (settings.LOGIN_URL,
                self.locale, path)
            self.assertRedirects(response, expected, status_code=302,
                                 target_status_code=301)

    def test_login_post(self):
        """Test logging in."""
        path = "/%s/login/" % (self.locale,)
        response = self.client.post(path, {
            'username': self.test_username,
            'password': self.test_password,
        })
        self.assertRedirects(response, '/en/home/dashboard/', status_code=302,
                             target_status_code=302)
        response2 = self.client.get(response["location"])
        self.client.logout()

        response5 = self.client.post(path, {
            'username': 'nonexistant',
            'password': 'password',
        })
        self.assertContains(response5, 'id="id_username"')

    def test_login_redirect_param(self):
        """Test that user is redirected properly after logging in."""
        path = "/%s/login/?%s=/%s/profile/edit/" % (
            self.locale, REDIRECT_FIELD_NAME, self.locale)
        response = self.client.post(path, {
            'username': self.test_username,
            'password': self.test_password,
        })
        self.assertEqual(
            "http://testserver/%s/profile/edit/" % (settings.LANGUAGE_CODE),
            response["location"],
        )

    def test_profile_image_directories(self):
        """Test that we partition image directories properly."""
        for i in range(1, 1001):
            p_id = get_partition_id(i)
            self.assertEqual(1, p_id)
        for i in range(1001, 2001):
            p_id = get_partition_id(i)
            self.assertEqual(2, p_id)
        for i in range(10001, 11001):
            p_id = get_partition_id(i)
            self.assertEqual(11, p_id)
        self.assertEqual(12, get_partition_id(11002))

    def test_protected_usernames(self):
        """
        Ensure that users cannot register using usernames that would conflict
        with other urlpatterns.
        """
        path = reverse('users_register')
        bad = ('groups', 'admin', 'people', 'about')
        for username in bad:
            response = self.client.post(path, {
                'username': username,
                'password': 'foobar123',
                'password_confirm': 'foobar123',
                'email': 'foobar123@example.com',
                'email_confirm': 'foobar123@example.com',
                'preflang': 'en'
            })
            self.assertContains(response, 'Please choose another')
        ok = self.client.post(path, {
            'username': 'iamtrulyunique',
            'password': 'foobar123',
            'password_confirm': 'foobar123',
            'email': 'foobar123@example.com',
            'email_confirm': 'foobar123@example.com',
            'preflang': 'en',
        })
        self.assertEqual(302, ok.status_code)

    def test_check_username_uniqueness(self):
        path = "/ajax/check_username/"
        existing = self.client.get(path, {
            'username': self.test_username,
        })
        self.assertEqual(200, existing.status_code)
        notfound = self.client.get(path, {
            'username': 'butterfly',
        })
        self.assertEqual(404, notfound.status_code)
