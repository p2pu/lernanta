from django import forms
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from projects.models import PerUserTaskCompletion
from badges.models import Submission

from content.models import Page


class OwnersPageForm(forms.ModelForm):

    """ field used to indicate that successful page creation should redirect here """
    next_url = forms.CharField(required=False,
        widget=forms.widgets.HiddenInput())
        
    class Meta:
        model = Page
        fields = ('title', 'sub_header', 'content',
            'collaborative', 'minor_update')

    def clean_title(self):
        data = self.cleaned_data.get('title')
        if len(slugify(data)) == 0:
            raise forms.ValidationError("Invalid title")
        return data


class PageForm(OwnersPageForm):

    class Meta(OwnersPageForm.Meta):
        exclude = ('collaborative',)


class NotListedPageForm(OwnersPageForm):

    class Meta(OwnersPageForm.Meta):
        exclude = ('title', 'collaborative',)


class OwnersNotListedPageForm(OwnersPageForm):

    class Meta(OwnersPageForm.Meta):
        exclude = ('title',)


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
