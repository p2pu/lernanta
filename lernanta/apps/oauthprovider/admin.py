from django.contrib import admin

from oauth2app.models import Client, Code

admin.site.register(Client)
admin.site.register(Code)
