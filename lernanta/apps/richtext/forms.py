from django import forms
from django.utils.translation import get_language
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.html import conditional_escape
from django.utils import simplejson
from django.utils.encoding import force_unicode

from ckeditor.widgets import CKEditorWidget as BaseCKEditorWidget

from l10n.urlresolvers import reverse

from richtext import clean_html, DEFAULT_CONFIG, CKEDITOR_CONFIGS


json_encode = simplejson.JSONEncoder().encode


class CKEditorWidget(BaseCKEditorWidget):

    def __init__(self, config_name='default', *args, **kwargs):
        super(CKEditorWidget, self).__init__(config_name, *args, **kwargs)
        self.config_name = config_name

    def render(self, name, value, attrs={}):
        self.config = DEFAULT_CONFIG.copy()
        self.config.update(CKEDITOR_CONFIGS[self.config_name])
        self.config['language'] = get_language()
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        self.config['filebrowserImageUploadUrl'] = reverse('ckeditor_upload')
        self.config['filebrowserImageBrowseUrl'] = reverse('ckeditor_browse')
        self.config['filebrowserUploadUrl'] = reverse('richtext_upload_file')
        self.config['filebrowserBrowseUrl'] = reverse('richtext_browse_file')
        return mark_safe(u'''<textarea%s>%s</textarea>
            <script type="text/javascript">
                var ckeditor_instance_id = "%s";
                if (CKEDITOR.instances[ckeditor_instance_id]) {
                    CKEDITOR.instances[ckeditor_instance_id].destroy();
                }
                CKEDITOR.replace(ckeditor_instance_id, %s);
            </script>''' % (flatatt(final_attrs),
            conditional_escape(force_unicode(value)),
            final_attrs['id'], json_encode(self.config)))


class RichTextFormField(forms.fields.Field):
    def __init__(self, config_name='default', *args, **kwargs):
        self.config_name = config_name
        kwargs.update({'widget': CKEditorWidget(config_name=config_name)})
        super(RichTextFormField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        value = super(RichTextFormField, self).to_python(value)
        value = clean_html(self.config_name, value)
        if value and value.strip() in ('<br />', '<br>'):
            value = u''
        elif not value:
            value = u''
        return value


class FileBrowser(forms.Form):
    CKEditorFuncNum = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, files, *args, **kwargs):
        super(FileBrowser, self).__init__(*args, **kwargs)
        self.fields['file'] = forms.ChoiceField(choices=files,
            widget=forms.RadioSelect)
