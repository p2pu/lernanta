from django.contrib import admin

from badges.models import Badge, Rubric, Award, Logic
from badges.models import Submission, Assessment, Rating


class BadgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    raw_id_fields = ('creator', 'prerequisites', 'rubrics',
        'groups')


class RubricAdmin(admin.ModelAdmin):
    list_display = ('id', 'question')


class AwardAdmin(admin.ModelAdmin):
    date_hierarchy = 'awarded_on'
    raw_id_fields = ('user', 'badge')
    list_display = ('id', 'badge', 'user')
    search_fields = ('id', 'badge__slug', 'badge__name', 'user__username',
        'user__full_name', 'user__email')


class LogicAdmin(admin.ModelAdmin):
    pass


class SubmissionAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'badge')


class AssessmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    raw_id_fields = ('assessor', 'assessed', 'badge', 'submission')
    list_display = ('id', 'badge', 'assessor', 'assessed', 'final_rating')
    search_fields = ('id', 'badge__slug', 'badge__name', 'assessor__username',
        'assessor__full_name', 'assessor__email', 'assessed__username',
        'assessed__full_name', 'assessed__email')


class RatingAdmin(admin.ModelAdmin):
    raw_id_fields = ('assessment', 'rubric')


admin.site.register(Badge, BadgeAdmin)
admin.site.register(Rubric, RubricAdmin)
admin.site.register(Award, AwardAdmin)
admin.site.register(Logic, LogicAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(Rating, RatingAdmin)
