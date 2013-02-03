import logging

from django import template
from django.utils.encoding import smart_str
from django.conf import settings

from l10n.urlresolvers import reverse

log = logging.getLogger(__name__)

register = template.Library()


class LocaleURLNode(template.Node):

    def __init__(self, node):
        self.node = node

    def render(self, context):
        args = [arg.resolve(context) for arg in self.node.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.node.kwargs.items()])
        return reverse(self.node.view_name, args=args, kwargs=kwargs)


@register.tag
def locale_url(parser, token):
    node = template.defaulttags.url(parser, token)
    return LocaleURLNode(node)


@register.simple_tag
def language_name(language_code):
    return dict(settings.LANGUAGES).get(language_code, language_code)
