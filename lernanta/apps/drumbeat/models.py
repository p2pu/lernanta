from django.db import models
from django.conf import settings

import caching.base
import logging

log = logging.getLogger(__name__)


class ManagerBase(caching.base.CachingManager, models.Manager):
    pass


class ModelBase(caching.base.CachingMixin, models.Model):
    objects = caching.base.CachingManager()

    class Meta:
        abstract = True
