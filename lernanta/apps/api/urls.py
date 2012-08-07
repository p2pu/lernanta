from django.conf.urls.defaults import *

from tastypie.api import Api
from apps.api.api import ProjectResource, UserProfileResource, SchoolResource, BadgeResource

alpha_api = Api(api_name='alpha')
alpha_api.register(ProjectResource())
alpha_api.register(UserProfileResource())
alpha_api.register(SchoolResource())
alpha_api.register(BadgeResource())

urlpatterns = patterns('',
    (r'', include(alpha_api.urls)),
)
