from django import forms
from django.utils.translation import ugettext as _

from users.models import UserProfile

from badges.models import Badge, Submission, Assessment, Rating


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ('name', 'description', 'image', 'rubrics')


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('url', 'content',)


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ('comment',)


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ('score',)
        widgets = {
            'score': forms.RadioSelect,
        }


class PeerAssessmentForm(forms.ModelForm):
    peer = forms.CharField()

    class Meta:
        model = Assessment
        fields = ('comment',)

    def __init__(self, badge, profile, *args, **kwargs):
        super(PeerAssessmentForm, self).__init__(*args, **kwargs)
        self.badge = badge
        self.profile = profile

    def clean_peer(self):
        username = self.cleaned_data['peer']
        if self.profile.username == username:
            raise forms.ValidationError(
                 _('You cannot give a badge to yourself.'))
        try:
            user = UserProfile.objects.get(username=username)
            if user.deleted:
                raise forms.ValidationError(
                    _('That user account was deleted.'))
        except UserProfile.DoesNotExist:
            raise forms.ValidationError(
                _('There is no user with username: %s.') % username)
        if not self.badge.get_peers(self.profile).filter(id=user.id).exists():
            raise forms.ValidationError(
                _('User %s needs to be your peer.') % username)
        if not self.badge.is_eligible(user):
            raise forms.ValidationError(
                _('User %s has not received all the prerequisite badges.') % username)
        return user
