import logging

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.db.models import Count

from links.models import Link
from users.models import UserProfile
from users.tasks import SendPrivateMessages
from tags.forms import GeneralTagField
from tags.models import GeneralTaggedItem
from schools.models import School

from projects.models import Project
from projects import drupal


log = logging.getLogger(__name__)


class ProjectForm(forms.ModelForm):
    tags = GeneralTagField(required=False)
    duration = forms.DecimalField(min_value=0, max_value=9000,
        decimal_places=1, required=False)

    def __init__(self, category, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.initial['tags'] = GeneralTaggedItem.objects.filter(
               object_id=instance.id)
            self.initial['duration'] = instance.get_duration()
        else:
            self.initial['duration'] = 0
        if category:
            self.fields['category'].required = False
        
        self.fields['name'].widget.attrs.update(
            {'placeholder': _('Write a catchy title, keep it short and sweet.')})
        self.fields['short_description'].widget.attrs.update(
            {'placeholder': _('e.g. Learn to write HTML by hand, literally.')})
        self.fields['long_description'].widget.attrs.update(
            {'placeholder': _("Who is the challenge for? <br>" \
                              "What are they going to be doing? <br>" \
                              "How are they going to be doing it? <br>" \
                              "Why are they doing it?")})
        self.fields['tags'].widget.attrs.update(
            {'placeholder': _('Tag your course so folks can find it. What will your audience be looking for? Separate with commas.')})

    class Meta:
        model = Project
        fields = ('test', 'name', 'category', 'other', 'other_description',
            'short_description', 'long_description', 'language')
        widgets = {
            'category': forms.RadioSelect,
        }

    def clean_other(self):
        other = self.cleaned_data.get('other')
        return other.strip() if other else other

    def save(self, commit=True):
        model = super(ProjectForm, self).save(commit=False)
        if commit:
            model.save()
            model.tags.set(*self.cleaned_data['tags'])
            model.save()
        return model


class ProjectLinksForm(forms.ModelForm):

    class Meta:
        model = Link
        fields = ('name', 'url', 'subscribe')


class ProjectImageForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ('image',)

    def clean_image(self):
        if self.cleaned_data['image'] and self.cleaned_data['image'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            msg = _("Image exceeds max image size: %(max)dk")
            raise forms.ValidationError(msg % dict(max=max_size))
        return self.cleaned_data['image']


class ProjectStatusForm(forms.ModelForm):

    start_date = forms.DateField(localize=True, required=False)
    end_date = forms.DateField(localize=True, required=False)

    duration = forms.DecimalField(min_value=0, max_value=9000,
        decimal_places=1, required=False)

    class Meta:
        model = Project
        fields = ('start_date', 'end_date', 'under_development',
            'not_listed', 'archived')


class ProjectAddParticipantForm(forms.Form):
    user = forms.CharField()
    organizer = forms.BooleanField(required=False)

    def __init__(self, project, *args, **kwargs):
        super(ProjectAddParticipantForm, self).__init__(*args, **kwargs)
        self.project = project

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
        # do not use is_organizing or is_participating here,
        # so superusers can join the study groups.
        if self.project.organizers().filter(user=user).exists():
            raise forms.ValidationError(
                _('User %s is already an organizer.') % username)
        is_participant = self.project.non_organizer_participants().filter(
            user=user).exists()
        if is_participant:
            raise forms.ValidationError(
                _('User %s is already a participant.') % username)
        return user


class ProjectAddNextProjectForm(forms.Form):
    next_project = forms.CharField()

    def __init__(self, project, *args, **kwargs):
        super(ProjectAddNextProjectForm, self).__init__(*args, **kwargs)
        self.project = project

    def clean_next_project(self):
        slug = self.cleaned_data['next_project']
        if slug == self.project.slug:
            msg = _('A %s can not be its own next step.')
            raise forms.ValidationError(msg % self.project.kind.lower())
        msg = _('There is no challenge, study group, ... with short name: %s.')
        try:
            next_project = Project.objects.get(slug=slug)
        except Project.DoesNotExist:
            raise forms.ValidationError(msg % slug)
        if self.project.next_projects.filter(slug=slug).exists():
            msg = _('The %(slug)s %(kind)s is already a next step.')
            raise forms.ValidationError(msg % {'slug': slug,
                'kind': next_project.kind.lower()})
        return next_project


class ProjectContactOrganizersForm(forms.Form):
    """
    A modified version of ``messages.forms.ComposeForm`` that enables
    authenticated users to send a message to all of the organizers.
    """
    project = forms.IntegerField(required=True, widget=forms.HiddenInput())
    subject = forms.CharField(label=_(u'Subject'))
    body = forms.CharField(
        label=_(u'Body'),
        widget=forms.Textarea(attrs={'rows': '12', 'cols': '55'}),
    )

    def save(self, sender, parent_msg=None):
        project = self.cleaned_data['project']
        try:
            project = Project.objects.get(id=int(project))
        except Project.DoesNotExist:
            raise forms.ValidationError(
                _('That study group, course, ... does not exist.'))
        recipients = project.organizers()
        subject = "[%s] " % project.name[:20] + self.cleaned_data['subject']
        body = render_to_string(
            "projects/emails/contact_organizer.txt", {
            'body': self.cleaned_data['body'],
            'domain': Site.objects.get_current().domain,
            'project': project}).strip()
        messages = [(sender, r.user.user, subject, body, parent_msg)
            for r in recipients]
        SendPrivateMessages.apply_async(args=(self, messages))
        return messages


class CloneProjectForm(forms.Form):
    project = forms.CharField()

    def clean_project(self):
        slug = self.cleaned_data['project']
        msg = _('There is no study group, course, ... with short name: %s.')
        try:
            project = Project.objects.get(slug=slug)
        except Project.DoesNotExist:
            raise forms.ValidationError(msg % slug)
        return project


class ImportProjectForm(forms.Form):
    course = forms.CharField()

    def clean_course(self):
        slug = self.cleaned_data['course']
        course = drupal.get_course(slug, full=True)
        if not course:
            raise forms.ValidationError(
                _('There is no course with this short name on the archive.'))
        return course


class ProjectsFilterForm(forms.Form):
    # Not Listed by Default
    archived = forms.BooleanField(required=False, widget=forms.HiddenInput)
    under_development = forms.BooleanField(required=False, widget=forms.HiddenInput)
    closed_signup = forms.BooleanField(required=False, widget=forms.HiddenInput)
    # Filter Links
    COMMUNITY = 'community'
    SHOWCASE = 'showcase'
    FRESH = 'fresh'
    POPULAR = 'popular'
    UPDATED = 'updated'
    FEATURED_CHOICES = (
        (COMMUNITY, _('Community Picks')),
        (SHOWCASE, _('Showcase')),
        (FRESH, _('Fresh Additions')),
        (POPULAR, _('Popular')),
        (UPDATED, _('Last Updated'))
    )
    featured = forms.ChoiceField(required=False, widget=forms.HiddenInput,
        choices=FEATURED_CHOICES)
    school = forms.ModelChoiceField(required=False, queryset=School.objects.all(),
        widget=forms.HiddenInput)
    tag = forms.CharField(required=False, widget=forms.HiddenInput)
    # Filter Form
    all_languages = forms.BooleanField(required=False)
    language = forms.ChoiceField(required=False, choices=settings.LANGUAGES)
    reviewed = forms.BooleanField(required=False)

    def __init__(self, projects, *args, **kwargs):
        super(ProjectsFilterForm, self).__init__(*args, **kwargs)
        existing_locales = set(loc for loc, lang in settings.LANGUAGES)
        locale_counts = projects.values('language').annotate(
            project_language_count=Count('id')).order_by()
        visible_locales = set(locale_counts.filter(
            project_language_count__gt=1).values_list(
            'language', flat=True))
        language_choices = tuple((loc, lang) for loc, lang in settings.LANGUAGES
            if loc in visible_locales and (len(loc) == 2 or loc[:2] not in existing_locales))
        self.fields['language'].widget.choices = language_choices
