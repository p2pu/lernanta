from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

from projects.models import Project
from users.models import UserProfile

from schools.models import School


class SchoolForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('name', 'short_name', 'description', 'more_info')


class SchoolStylesForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('headers_color', 'headers_color_light', 'background_color',
            'menu_color', 'menu_color_light', 'sidebar_width',
            'show_school_organizers', 'extra_styles',)


class SchoolLogoForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('logo',)

    def clean_logo(self):
        if self.cleaned_data['logo'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            msg = _("Image exceeds max image size: %(max)dk")
            raise forms.ValidationError(msg % dict(max=max_size))
        return self.cleaned_data['logo']


class SchoolGroupsIconForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('groups_icon',)

    def clean_groups_icon(self):
        if self.cleaned_data['groups_icon'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            msg = _("Image exceeds max image size: %(max)dk")
            raise forms.ValidationError(msg % dict(max=max_size))
        return self.cleaned_data['groups_icon']


class SchoolBackgroundForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('background',)

    def clean_groups_icon(self):
        if self.cleaned_data['background'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            msg = _("Image exceeds max image size: %(max)dk")
            raise forms.ValidationError(msg % dict(max=max_size))
        return self.cleaned_data['background']


class SchoolSiteLogoForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('site_logo',)

    def clean_groups_icon(self):
        if self.cleaned_data['site_logo'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            msg = _("Image exceeds max image size: %(max)dk")
            raise forms.ValidationError(msg % dict(max=max_size))
        return self.cleaned_data['site_logo']


class ProjectAddOrganizerForm(forms.Form):
    user = forms.CharField()

    def __init__(self, school, *args, **kwargs):
        super(ProjectAddOrganizerForm, self).__init__(*args, **kwargs)
        self.school = school

    def clean_user(self):
        username = self.cleaned_data['user']
        try:
            user = UserProfile.objects.get(username=username)
            if user.deleted:
                raise forms.ValidationError(
                    _('That user account was deleted.'))
        except UserProfile.DoesNotExist:
            raise forms.ValidationError(
                _('There is no user with username: %s.') % username)
        if self.school.organizers.filter(id=user.id).exists():
            raise forms.ValidationError(
                _('User %s is organizing the school.') % username)
        return user


class SchoolAddCourseForm(forms.Form):
    course_url = forms.CharField()


class SchoolMentorshipForm(forms.ModelForm):

    class Meta:
        model = School
        fields = ('mentor_form_url', 'mentee_form_url',)
