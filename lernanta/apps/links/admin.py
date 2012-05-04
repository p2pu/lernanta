from django.contrib import admin
from links.models import Link


class LinkAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'user', 'subscription')
    list_display = ('id', 'name', 'url', 'project', 'user', 'index',
        'subscribe')
    list_filter = list_display[6:]
    search_fields = ('id', 'name', 'url', 'project__name', 'project__slug',
        'user__username', 'user__full_name', 'index')

admin.site.register(Link, LinkAdmin)
