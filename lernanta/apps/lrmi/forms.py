from django import forms
from django.utils.translation import ugettext as _


class LrmiForm(forms.Form):

    EDUCATIONAL_ROLE_CHOICES = [
        ('', 'not set'),
        ('student', 'Students'),
        ('teacher', 'Teachers'),
    ]

    INTERACTIVITY_CHOICES = [
        ('', 'not set'),
        ('active', 'Active'),
        ('expositive', 'Expositive'),
        ('mixed', 'Mixed'),
    ]

    educationalrole = forms.ChoiceField(required=False, choices=EDUCATIONAL_ROLE_CHOICES)
    educationaluse = forms.CharField(max_length=255, required=False)
    timerequired = forms.CharField(max_length=255, required=False)
    typicalagerange = forms.CharField(max_length=255, required=False)
    interactivitytype = forms.ChoiceField(required=False, choices=INTERACTIVITY_CHOICES)
    isbasedonurl = forms.URLField(max_length=255, required=False)
    about = forms.CharField(max_length=255, required=False)


class EducationalAlignmentForm(forms.Form):

    alignmenttype  = forms.CharField(max_length=255, required=True, label=_('Alignment Type'))

    educationalframework = forms.CharField(max_length=255, required=False, label=_('Educational Framework'))

    targetdescription = forms.CharField(max_length=255, required=False, label=_('Target Description'))

    targetname = forms.CharField(max_length=255, required=False, label=_('Target Name'))
    
    targeturl = forms.URLField(max_length=255, required=False, label=_('Target URL'))
