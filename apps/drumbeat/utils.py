import os
import re
import math
import hashlib
import unicodedata

from django.core.validators import ValidationError, validate_slug
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language, ugettext
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils import simplejson

from l10n.urlresolvers import reverse

from ckeditor.widgets import CKEditorWidget as BaseCKEditorWidget


json_encode = simplejson.JSONEncoder().encode


# Some utility functions shamelessly lifted from zamboni

# Extra characters outside of alphanumerics that we'll allow.
SLUG_OK = '-_'


def slugify(s, ok=SLUG_OK, lower=True):
    # L and N signify letter/number.
    # http://www.unicode.org/reports/tr44/tr44-4.html#GC_Values_Table
    rv = []
    for c in smart_unicode(s):
        cat = unicodedata.category(c)[0]
        if cat in 'LN' or c in ok:
            rv.append(c)
        if cat == 'Z':  # space
            rv.append(' ')
    new = re.sub('[-\s]+', '-', ''.join(rv).strip())
    return new.lower() if lower else new


def slug_validator(s, ok=SLUG_OK, lower=True):
    """
    Raise an error if the string has any punctuation characters.

    Regexes don't work here because they won't check alnums in the right
    locale.
    """
    if not (s and slugify(s, ok, lower) == s):
        raise ValidationError(validate_slug.message,
                              code=validate_slug.code)


def get_partition_id(pk, chunk_size=1000):
    """
    Given a primary key and optionally the number of models that will get
    shared access to a directory, return an integer representing a directory
    name.
    """
    return int(math.ceil(pk / float(chunk_size)))


def safe_filename(filename):
    """Generate a safe filename for storage."""
    name, ext = os.path.splitext(filename)
    return "%s%s" % (hashlib.md5(name.encode('utf8')).hexdigest(), ext)


class CKEditorWidget(BaseCKEditorWidget):
    def __init__(self, *args, **kwargs):
        super(CKEditorWidget, self).__init__(*args, **kwargs)
        # Temporary bug fix in CKEDITOR widget (do not share configuration).
        self.config = self.config.copy()

    def render(self, name, value, attrs={}):
        if value is None: value = ''
        
        # Not charing locale info between different instance of the form.
        config = self.config.copy()
        config['language'] = get_language()
        
        final_attrs = self.build_attrs(attrs, name=name)
        self.config['filebrowserUploadUrl'] = reverse('ckeditor_upload')
        self.config['filebrowserBrowseUrl'] = reverse('ckeditor_browse')
        return mark_safe(u'''<textarea%s>%s</textarea>
        <script type="text/javascript">
            CKEDITOR.replace("%s", %s);
        </script>''' % (flatatt(final_attrs), conditional_escape(force_unicode(value)), final_attrs['id'], json_encode(config)))
