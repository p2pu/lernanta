from django.contrib import admin
from django.utils.translation import ugettext as _

from schools.models import School, ProjectSet, ProjectSetIndex


class SchoolAdmin(admin.ModelAdmin):
    raw_id_fields = ('organizers', 'featured')
    list_display = ('id', 'name',)
    search_fields = ('id', 'name',)


class ProjectSetIndexInline(admin.TabularInline):
    model = ProjectSetIndex
    raw_id_fields = ('project',)


class ProjectSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school',)
    search_fields = ('id', 'name', 'school__name',)
    inlines = (ProjectSetIndexInline,)


admin.site.register(School, SchoolAdmin)
admin.site.register(ProjectSet, ProjectSetAdmin)
