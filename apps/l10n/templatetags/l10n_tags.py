from django import template
from django.utils.encoding import smart_str

from l10n.urlresolvers import reverse

import logging
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
