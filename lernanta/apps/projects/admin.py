from django.contrib import admin

from drumbeat.views import export_as_csv

from projects.models import Project, Participation


class ProjectAdmin(admin.ModelAdmin):
    actions = [export_as_csv]
    raw_id_fields = ('detailed_description', 'next_projects',
        'completion_badges', 'clone_of')
    date_hierarchy = 'created_on'
    list_display = ('id', 'name', 'slug', 'clone_of', 'language', 'created_on')
    list_filter = ('school', 'featured', 'under_development', 'not_listed',
        'archived', 'deleted', 'test')
    search_fields = ('id', 'name', 'slug', 'school__name',
        'clone_of__slug', 'clone_of__name', 'language')


class ParticipationAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'user')
    date_hierarchy = 'joined_on'
    list_display = ('id', 'user', 'project', 'organizing', 'joined_on',
        'left_on', 'no_organizers_wall_updates',
        'no_organizers_content_updates', 'no_participants_wall_updates',
        'no_participants_content_updates')
    list_filter = list_display[3:]
    search_fields = ('id', 'project__name', 'user__username',
        'user__full_name', 'project__slug')

admin.site.register(Project, ProjectAdmin)
admin.site.register(Participation, ParticipationAdmin)
