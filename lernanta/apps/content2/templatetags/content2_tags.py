from django import template
from django.template.defaultfilters import stringfilter

import markdown
import bleach
from html5lib.tokenizer import HTMLTokenizer

register = template.Library()

@register.filter
@stringfilter
def convert_content( markdown_text ):
    html = markdown.markdown(markdown_text, ['tables'])
    html = bleach.linkify(html, target="_blank", tokenizer=HTMLTokenizer)
    return html

convert_content.is_safe = True
