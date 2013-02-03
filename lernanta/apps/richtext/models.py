import datetime

from django.db import models
from django.utils import simplejson as json

from ckeditor.fields import RichTextField as BaseRichTextField
from south.modelsinspector import add_introspection_rules

from drumbeat.models import ModelBase

from richtext.forms import RichTextFormField
from richtext import clean_html


class RichTextField(BaseRichTextField):

    def formfield(self, **kwargs):
        return super(RichTextField, self).formfield(
            form_class=RichTextFormField, **kwargs)

    def pre_save(self, model_instance, add):
        value = super(RichTextField, self).pre_save(model_instance, add)
        setattr(model_instance, self.attname, clean_html(self.config_name,
            value))
        return value

add_introspection_rules([], ["^richtext\.models\.RichTextField"])


class JSONField(models.TextField):
    # Extracted from django/trunk/tests/modeltests/field_subclassing/fields.py
    __metaclass__ = models.SubfieldBase

    description = ("JSONField automatically serializes and "
        "desializes values to and from JSON.")

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, basestring):
            value = json.loads(value)
        return value

    def get_db_prep_save(self, value, connection):
        if value is None:
            return None
        return json.dumps(value)

add_introspection_rules([], ["^richtext\.models\.JSONField"])


class EmbeddedUrl(ModelBase):
    original_url = models.URLField(max_length=1023)
    html = models.TextField()
    extra_data = JSONField() #This field doesn't seem to be used!
    created_on = models.DateTimeField(
        auto_now_add=True, default=datetime.datetime.now)
