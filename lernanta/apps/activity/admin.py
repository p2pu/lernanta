from django.contrib import admin

from activity.models import Activity, RemoteObject

class ActivityAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    raw_id_fields = ('actor', 'scope_object', 'target_content_type')
    list_display = ('id', 'actor', 'scope_object')
    list_filter = ('deleted',)
    search_fields = ('id', 'actor__username', 'actor__full_name',
        'actor__email', 'scope_object__slug', 'scope_object__name')


class RemoteObjectAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    raw_id_fields = ('link',)
    list_display = ('id', 'link', 'title', 'uri', 'created_on')
    search_fields = ('id', 'link__name', 'link__url')


admin.site.register(Activity, ActivityAdmin)
admin.site.register(RemoteObject, RemoteObjectAdmin)
