from django.contrib import admin
from users.models import UserProfile, TaggedProfile


class UserProfileAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    list_display = ('id', 'username', 'full_name', 'email', 'location',
        'preflang', 'featured', 'created_on')
    list_filter = list_display[5:]
    search_fields = list_display[:5]


class TaggedProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('tag',)
    list_display = ('id', 'tag')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(TaggedProfile, TaggedProfileAdmin)
