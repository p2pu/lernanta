from django.db import models

class MetaTag(models.Model):
    item_uri = models.CharField(max_length=256)
    key = models.CharField(max_length=256)
    value = models.CharField(max_length=4096)
