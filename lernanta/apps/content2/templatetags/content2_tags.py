from django import template
from django.template.defaultfilters import stringfilter

import markdown
import bleach
from html5lib.tokenizer import HTMLTokenizer
import re

register = template.Library()

@register.filter
@stringfilter
def convert_content( markdown_text ):
    html = markdown.markdown(markdown_text, ['tables'])
    html = bleach.linkify(html, target="_blank", tokenizer=HTMLTokenizer)
    regex = re.compile(r'<pre\>.*?</pre\>', re.IGNORECASE|re.DOTALL)
    f = lambda m: re.sub(r'&amp;', '&', m.group(0))
    html = regex.sub(f, html)
    return html

convert_content.is_safe = True
