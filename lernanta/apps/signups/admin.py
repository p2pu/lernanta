from django.contrib import admin

from signups.models import Signup, SignupAnswer


class SignupAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'author')
    list_display = ('id', 'project', 'status')
    list_filter = list_display[2:]
    search_fields = ('id', 'project__slug', 'project__name')


class SignupAnswerAdmin(admin.ModelAdmin):
    raw_id_fields = ('sign_up', 'author')
    date_hierarchy = 'created_on'
    list_display = ('id', 'author', 'project',
        'created_on', 'accepted', 'deleted')
    list_filter = list_display[3:]
    search_fields = ('id', 'author__username', 'author__full_name',
        'sign_up__project__slug', 'sign_up__project__name')

admin.site.register(Signup, SignupAdmin)
admin.site.register(SignupAnswer, SignupAnswerAdmin)
