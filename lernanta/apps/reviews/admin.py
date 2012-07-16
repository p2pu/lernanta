from django.contrib import admin

from reviews.models import Review, Reviewer


class ReviewerAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)


class ReviewAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'author')


admin.site.register(Reviewer, ReviewerAdmin)
admin.site.register(Review, ReviewAdmin)
