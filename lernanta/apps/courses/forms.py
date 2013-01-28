from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.forms.widgets import RadioSelect

class CourseCreationForm(forms.Form):
    title = forms.CharField()
    hashtag = forms.CharField(max_length=20)
    description = forms.CharField(widget=forms.Textarea)
    language = forms.ChoiceField(choices=settings.LANGUAGES)

    def clean_hashtag(self):
        return self.cleaned_data['hashtag'].strip('#')


class CourseUpdateForm(forms.Form):
    title = forms.CharField(required=False)
    hashtag = forms.CharField(required=False, max_length=20)
    description = forms.CharField(widget=forms.Textarea, required=False)
    language = forms.ChoiceField(choices=settings.LANGUAGES, required=False)

    def clean_hashtag(self):
        return self.cleaned_data['hashtag'].strip('#')


class CourseImageForm(forms.Form):
    image = forms.ImageField()


class CourseTermForm(forms.Form):
    start_date = forms.DateField()
    end_date = forms.DateField()


class CourseTagsForm(forms.Form):
    tags = forms.CharField(max_length=256)


SIGNUP_CHOICES = [
    ("OPEN", _("Open"),), 
    ("MODERATED", _("Moderated"),),
    ("CLOSED", _("Closed"),)
]

class CohortSignupForm(forms.Form):
    signup = forms.ChoiceField(choices=SIGNUP_CHOICES, widget=RadioSelect)
