from django.contrib import admin
from schools.models import School, ProjectSet


class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('id', 'name',)

admin.site.register(School, SchoolAdmin)


class ProjectSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school',)
    search_fields = ('id', 'name', 'school__name',)

admin.site.register(ProjectSet, ProjectSetAdmin)
