from django.db import models

from drumbeat.models import ModelBase


class Content(ModelBase):

    latest = models.ForeignKey('content2.ContentVersion', related_name='+', null=True, blank=True)
    based_on = models.ForeignKey('content2.Content', related_name='derived_content', null=True, blank=True)


class ContentVersion(ModelBase):

    container = models.ForeignKey(Content, related_name='versions')
    title = models.CharField(max_length = 100)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length = 100)
    author_uri = models.CharField(max_length=256)
