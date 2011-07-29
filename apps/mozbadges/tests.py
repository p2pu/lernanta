import re
import json
from django.test import TestCase
from django.conf import settings
from urllib2 import urlopen, HTTPError, URLError

import utils

class SettingsTests(TestCase):
    def test_existence(self):
        self.assertTrue(hasattr(settings, 'MOZBADGES'), 'Settings missing MOZBADGES attribute')
        self.assertTrue(isinstance(settings.MOZBADGES, dict), 'settings.MOZBADGES should be a dict')

    def test_hub(self):
        # url regex taken from http://mathiasbynens.be/demo/url-regex,
        # using the @stephenhay method.
        url_re = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.I)
        hub_uri = settings.MOZBADGES.get('hub', '')
        
        self.assertTrue(url_re.match(hub_uri), "settings.MOZBADGES['hub'] must be valid http(s) uri.")
        
        try:
            # get the status url
            resp = urlopen('%s/_status' % hub_uri)
            httpstatus = resp.getcode()
            hubstatus = json.loads(resp.read())['status']
            
            self.assertEqual(httpstatus, 200, "Expecting HTTP 200 from hub, got %s" % httpstatus)
            self.assertEqual(hubstatus, 'okay', "Got 200, but received unexpected response body")
        except URLError, e:
            self.assertTrue(False, "Valid looking uri, but could not lookup. Problem may be temporary.")
        except HTTPError, e:
            self.assertTrue(False, "Expecting HTTP 200 from hub, got %s" % httpstatus)

    def test_badge_getter(self):
        q_getter = settings.MOZBADGES.get('badge_getter', '')
        self.assertTrue(q_getter, "settings.MOZBADGES['badge_getter'] must be set.")
        
        self.assertIn('.', q_getter, "settings.MOZBADGES['badge_getter'] method probably shouldn't be top level.")
        
        method = utils.process_getter(q_getter)
        self.assertTrue(callable(method), "%s not a callable object." % q_getter)
