from django.contrib import admin

from content.models import Page, PageVersion


class PageAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'project', 'badges_to_apply')
    date_hierarchy = 'last_update'
    list_display = ('id', 'title', 'author', 'project', 'index', 'last_update',
        'listed', 'collaborative', 'deleted')
    list_filter = list_display[5:]
    search_fields = ('id', 'title', 'slug', 'project__slug', 'project__name',
        'author__username', 'author__full_name')


class PageVersionAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'page')
    date_hierarchy = 'date'
    list_display = ('id', 'page', 'author', 'date', 'deleted')
    list_filter = list_display[3:]
    search_fields = ('id', 'page__slug', 'page__title',
        'author__username', 'author__full_name')


admin.site.register(Page, PageAdmin)
admin.site.register(PageVersion, PageVersionAdmin)
