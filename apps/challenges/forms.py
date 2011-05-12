import logging

from django import forms
from django.conf import settings
from django.forms.extras.widgets import SelectDateWidget
from django.utils.translation import ugettext_lazy as _

from challenges.models import (Challenge, Submission, Judge,
                               VoterTaxonomy, VoterDetails)

log = logging.getLogger(__name__)


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        exclude = ('slug', 'project', 'created_by', 'created_on', 'is_open')
        widgets = {
            'start_date': SelectDateWidget(),
            'end_date': SelectDateWidget(),
        }


class ChallengeImageForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ('image',)

    def clean_image(self):
        if self.cleaned_data['image'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            raise forms.ValidationError(
                _("Image exceeds max image size: %(max)dk" % dict(max=max_size)))
        return self.cleaned_data['image']


class SubmissionSummaryForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('summary', )


class SubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('title', 'summary', 'keywords', 'bio')


class SubmissionDescriptionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ('description', )
        widgets = {
            'description': forms.Textarea(attrs={'class': 'wmd'}),
        }


class VoterDetailsForm(forms.ModelForm):
    taxonomy = forms.ModelMultipleChoiceField(
        queryset=VoterTaxonomy.objects.all(),
        required=True, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = VoterDetails
        fields = ('taxonomy', )

    def clean_taxonomy(self):
        if len(self.cleaned_data['taxonomy']) > 3:
            raise forms.ValidationError('Select no more than 3.')
        return self.cleaned_data['taxonomy']


class JudgeForm(forms.ModelForm):
    class Meta:
        model = Judge
        fields = ('user', )
