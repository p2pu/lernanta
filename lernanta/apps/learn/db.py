import datetime

from django.db import models


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=1000)
    url = models.URLField() #TODO <- this should be unique
    data_url = models.URLField()
    thumbnail_url = models.URLField()
    language = models.CharField(max_length=10)
    verified = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True, default=datetime.datetime.utcnow)
    date_checked = models.DateTimeField(null=True)
    date_removed = models.DateTimeField(null=True)


class List(models.Model):
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    url = models.URLField()


class CourseListEntry(models.Model):
    course_list = models.ForeignKey(List)
    course = models.ForeignKey(Course)


class CourseTags(models.Model):
    tag = models.CharField(max_length=100)
    course = models.ForeignKey(Course)
    internal = models.BooleanField(default=False)
