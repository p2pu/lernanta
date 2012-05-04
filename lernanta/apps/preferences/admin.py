from django.contrib import admin
from preferences.models import AccountPreferences


class AccountPreferencesAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('id', 'user', 'key', 'value',)
    list_filter = ('key',)
    search_fields = ('id', 'user__username', 'user__full_name',)

admin.site.register(AccountPreferences, AccountPreferencesAdmin)
