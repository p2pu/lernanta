from django.contrib import admin
from statuses.models import Status


class StatusAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'project')
    date_hierarchy = 'created_on'
    list_display = ('id', 'author', 'project', 'created_on', 'important')
    list_filter = list_display[3:]
    search_fields = ('id', 'author__username', 'author__full_name',
        'project__slug', 'project__name')

admin.site.register(Status, StatusAdmin)
