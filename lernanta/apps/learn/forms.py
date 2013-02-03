from django import forms
from django.utils.translation import ugettext as _

from learn.models import get_active_languages

class CourseFilterForm(forms.Form):
    # Not Listed by Default
    archived = forms.BooleanField(required=False, widget=forms.HiddenInput)
    under_development = forms.BooleanField(required=False, widget=forms.HiddenInput)
    closed_signup = forms.BooleanField(required=False, widget=forms.HiddenInput)
    
    language = forms.ChoiceField(required=False, choices=[('all', 'All')] + get_active_languages())
    reviewed = forms.BooleanField(required=False)

