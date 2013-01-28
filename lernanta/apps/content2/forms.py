from django import forms
from content2 import utils

class ContentForm(forms.Form):
    title = forms.CharField(max_length=80)
    content = forms.CharField(widget=forms.Textarea, required=False)

    def clean_content(self):
        return utils.clean_user_content(self.cleaned_data['content'])
