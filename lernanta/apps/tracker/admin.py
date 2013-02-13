from django.contrib import admin

from tracker.models import GoogleAnalyticsTrackingCode, GoogleAnalyticsTracking

class GoogleAnalyticsTrackingCodeAdmin(admin.ModelAdmin):
    pass

class GoogleAnalyticsTrackingAdmin(admin.ModelAdmin):
    pass

admin.site.register(GoogleAnalyticsTrackingCode, GoogleAnalyticsTrackingCodeAdmin)
admin.site.register(GoogleAnalyticsTracking, GoogleAnalyticsTrackingAdmin)



