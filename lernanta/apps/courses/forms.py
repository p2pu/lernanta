from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import RadioSelect

import re

class HashtagField(forms.CharField):
    def clean(self, value):
        if not value:
            return super(HashtagField, self).clean(value)
        if not re.match('^[#]*[a-z,A-Z][a-z,A-Z,0-9,_,-]*$', value):
            raise forms.ValidationError(_("The hashtag must start with letter and contain only letters, digits, _ and -"))
        return super(HashtagField, self).clean(value.strip('#'))


class CourseCreationForm(forms.Form):
    title = forms.CharField()
    hashtag = HashtagField(max_length=20)
    description = forms.CharField(widget=forms.Textarea)
    language = forms.ChoiceField(choices=settings.LANGUAGES)


class CourseUpdateForm(forms.Form):
    title = forms.CharField(required=False)
    hashtag = HashtagField(required=False, max_length=20)
    description = forms.CharField(widget=forms.Textarea, required=False)
    language = forms.ChoiceField(choices=settings.LANGUAGES, required=False)


class CourseImageForm(forms.Form):
    image = forms.ImageField()


class CourseTermForm(forms.Form):
    start_date = forms.DateField()
    end_date = forms.DateField()


class CourseTagsForm(forms.Form):
    tags = forms.CharField(max_length=256)


class CourseEmbeddedUrlForm(forms.Form):
    url = forms.URLField(max_length=300)


class CourseStatusForm(forms.Form):
    STATUS_CHOICES = [
        ('draft', _('Draft'), ),
        ('published', _('Published'), ),
        ('archived', _('Archived'), ),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=RadioSelect)


SIGNUP_CHOICES = [
    ("OPEN", _("Open"),), 
    ("MODERATED", _("Moderated"),),
    ("CLOSED", _("Closed"),)
]

class CohortSignupForm(forms.Form):
    signup = forms.ChoiceField(choices=SIGNUP_CHOICES, widget=RadioSelect)
