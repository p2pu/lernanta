from tastypie.resources import ModelResource
from tastypie import fields
from projects.models import Project
from users.models import UserProfile
from schools.models import School
from badges.models import Badge
from django.conf.urls.defaults import url 


class UserProfileResource(ModelResource):
    class Meta:
        queryset = UserProfile.objects.all()
        fields = ['username', 'bio', 'gravatar', 'following', 'followers',
            'skills']
        resource_name = 'users'
        
    def dehydrate(self, bundle):
        bundle.data['gravatar'] = bundle.obj.gravatar()
        bundle.data['following'] = bundle.obj.get_current_projects()
        bundle.data['followers'] = bundle.obj.followers()
        bundle.data['skills'] = map( lambda profile_tag: profile_tag.name,
            bundle.obj.tags.filter(category='skill') )

        return bundle

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<username>[\w\d\s_.-]+)/$" 
                % self._meta.resource_name, self.wrap_view('dispatch_detail'), 
                name="api_dispatch_detail"), 
        ]

class SchoolResource(ModelResource):
    class Meta:
        queryset = School.objects.all()


class BadgeResource(ModelResource):
    class Meta:
        queryset = Badge.objects.all()


class ProjectResource(ModelResource):
    school = fields.ForeignKey(SchoolResource, 'school', null=True)
    completion_badges = fields.ToManyField(BadgeResource, 'badges', null=True)

    class Meta:
        queryset = Project.objects.all()
        fields = ['school', 'category', 'community_featured', 'created_on',
                'duration_hours', 'end_date', 'featured', 'image', 'language',
                'long_description', 'name', 'other', 'other_description',
                'resource_uri', 'short_description', 'slug', 'start_date',
                'completion_badges']
        resource_name = 'courses'
