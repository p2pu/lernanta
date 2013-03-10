from django.db import models

import datetime
import random
import string


def _gen_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(32))


class ResponseToken(models.Model):
    """ Store response tokens and callbacks """

    # Unique token used to route response coming in via email
    response_token = models.CharField(max_length=32, blank=False)

    # URL to call when receiving a response
    response_callback = models.CharField(max_length=255, blank=False)

    # Date that the token was created
    creation_date = models.DateTimeField(auto_now_add=True,
        default=datetime.datetime.now, blank=False)

    def save(self):
        """Generate response token."""
        if not self.response_token:
            self.response_token = _gen_token()
            while True:
                existing = ResponseToken.objects.filter(
                    response_token=self.response_token
                ).count()
                if existing == 0:
                    break
                self.response_token = _gen_token()
        super(ResponseToken, self).save()


    def __unicode__(self):
        return self.response_token

