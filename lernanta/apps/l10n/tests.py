import re

from django.conf import settings
from django.test import Client
from django.contrib.auth.models import User

from users.models import create_profile
from l10n import locales

import test_utils


class TestLocaleURLs(test_utils.TestCase):

    def setUp(self):
        self.client = Client()
        locales.LOCALES['de-DE'] = locales.Language(
            external=u'de-DE',
            internal=u'de',
            english=u'German',
            native=u'Deutsch',
            dictionary='de-DE',
        )

        locales.INTERNAL_MAP = dict(
            [(locales.LOCALES[k].internal, k) for k in locales.LOCALES])
        locales.LANGUAGES = dict(
            [(i.lower(), locales.LOCALES[i].native) for i in locales.LOCALES])
        locales.LANGUAGE_URL_MAP = dict(
            [(i.lower(), i) for i in locales.LOCALES])

    def test_default_rewrites(self):
        """Test that the client gets what they ask for if it's supported."""
        for supported in locales.LOCALES.keys():
            response = self.client.get('/', HTTP_ACCEPT_LANGUAGE=supported)
            self.assertRedirects(response, '/%s/' % (supported,),
                                 status_code=301)

    def test_general(self):
        """
        If the client sends a specific locale that is unsupported, we
        should check for a more general match (xx-YY -> xx).
        """
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='es-CO')
        self.assertRedirects(response, '/es/', status_code=301)

    def test_unsupported_locale(self):
        """If locale is not supported, we should send them the default."""
        # if the default locale is not normalized, we'll get an additional 301
        default_locale = settings.LANGUAGE_CODE
        is_normalized = lambda l: re.match(r'[a-z]+(-[A-Z]+)?', l) != None
        expected_target_code = is_normalized(default_locale) and 200 or 301
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='xx')
        self.assertRedirects(response,
                             '/%s/' % (default_locale,),
                             status_code=301,
                             target_status_code=expected_target_code)

    def test_normalized_case(self):
        """Accept-Language header is case insensitive."""
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='en-us')
        self.assertRedirects(response, '/en/', status_code=301,
            target_status_code=200)

    def test_login_post_redirect(self):
        """Test that post requests are treated properly."""
        django_user = User(
            username='testuser',
            email='test@mozilla.com',
        )
        user = create_profile(django_user)
        user.set_password('testpass')
        user.save()
        response = self.client.get('/de-DE/login/')
        self.assertContains(response, 'csrfmiddlewaretoken')
        response = self.client.post('/de-DE/login/', {
            'username': user.username,
            'password': 'testpass',
        })
        self.assertRedirects(response, '/en/dashboard/', status_code=302,
                             target_status_code=302)
