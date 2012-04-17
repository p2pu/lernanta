from django import forms
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from projects.models import PerUserTaskCompletion
from badges.models import Submission

from content.models import Page


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ('title', 'sub_header', 'content', 'minor_update',)


class NotListedPageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ('content', 'sub_header', 'minor_update',)


class OwnersPageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ('title', 'sub_header', 'content',
            'collaborative', 'minor_update')

    def clean_title(self):
        data = self.cleaned_data.get('title')
        if len(slugify(data)) == 0:
            raise forms.ValidationError("Invalid title")
        return data


class OwnersNotListedPageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ('content', 'sub_header', 'collaborative', 'minor_update')


class TaskLinkSubmitForm(forms.ModelForm):
    post_link = forms.BooleanField(required=False, initial=True)

    def __init__(self, show_badge_apply_option, *args, **kwargs):
        super(TaskLinkSubmitForm, self).__init__(*args, **kwargs)
        if show_badge_apply_option:
            self.fields['apply_for_badges'] = forms.BooleanField(required=False, initial=False)
        self.fields['url'].widget.attrs.update({'placeholder': _('Post a link to your work.')})
        self.fields['url'].required = True
        self.fields['url'].widget.is_required = True

    class Meta:
        model = PerUserTaskCompletion
        fields = ('url',)


class TaskBadgeApplyForm(forms.ModelForm):
    badge_slug = forms.SlugField(widget=forms.HiddenInput())

    class Meta:
        model = Submission
        fields = ('content',)
