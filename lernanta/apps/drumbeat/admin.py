from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site

from django_openid_auth.models import Nonce, Association, UserOpenID
from djcelery.models import TaskState, PeriodicTask, CrontabSchedule
from djcelery.models import IntervalSchedule, WorkerState
from taggit.models import Tag
from wellknown.models import Resource
from voting.models import Vote
from drumbeatmail.models import Message


admin.site.unregister([Nonce, Association, UserOpenID,
    TaskState, PeriodicTask, CrontabSchedule, IntervalSchedule, WorkerState,
    Tag, Resource, Vote, Site])


admin.site._registry[User].date_hierarchy = 'date_joined'
admin.site._registry[User].list_display = ('id', 'username', 'email', 'is_active',
    'is_staff', 'is_superuser')
admin.site._registry[User].list_display_links = ('id',)
admin.site._registry[User].search_fields = ('id', 'username', 'email')


admin.site._registry[Message].raw_id_fields = ('sender', 'parent_msg')
admin.site._registry[Message].date_hierarchy = 'sent_at'
admin.site._registry[Message].list_display = ('id', 'subject', 'sender',
    'recipient', 'sent_at')
admin.site._registry[Message].list_filter = ('sent_at',)
admin.site._registry[Message].search_fields = ('id', 'subject', 'body',
    'sender__username', 'recipient__username')
