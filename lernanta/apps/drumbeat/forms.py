from django import forms


class AbuseForm(forms.Form):
    pass


class AbuseReasonForm(forms.Form):

    REASONS = (
        ('spam', 'Spam'),
        ('offensive', 'Offensive'),
        ('other', 'Other')
    )

    url = forms.CharField()
    reason = forms.ChoiceField(choices=REASONS)
    other = forms.CharField(max_length=255, required=False)
