import re
from datetime import datetime

from django.template.defaultfilters import stringfilter
from django import template
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from embedly import Embedly

from richtext.models import EmbeddedUrl


register = template.Library()


EMBED_RE = (r"\[(?P<kind>slideshare|youtube|embed|externaltask):(?P<url>[^\]]+)]")
url_validate = URLValidator(verify_exists=True)


def replace(match):
    url = match.group('url')
    kind = match.group('kind')
    external_task = (match.group('kind') == 'externaltask')
    try:
        url_validate(url)
    except ValidationError:
        return '[%s:Invalid Url]' % kind
    for prefix in settings.P2PU_EMBEDS:
        if url.startswith(prefix):
            return render_to_string('richtext/_p2pu_embed.html', {'url': url})
    if not external_task:
        expiration_date = datetime.now() - settings.EMBEDLY_CACHE_EXPIRES
        embedded_urls = EmbeddedUrl.objects.filter(original_url=url,
            created_on__gte=expiration_date).order_by('-created_on')
        embedded_url = None
        if embedded_urls.exists():
            embedded_url = embedded_urls[0]
        else:
            embedly_key = getattr(settings, 'EMBEDLY_KEY', False)
            if embedly_key:
                client = Embedly(embedly_key)
                obj = client.oembed(url, maxwidth=460)
                extra_data = obj.dict
                if 'dominant_colors' in extra_data:
                    del extra_data['dominant_colors']
                embedded_url = EmbeddedUrl(original_url=obj.original_url,
                    html=(obj.html or ''), extra_data=extra_data)
                embedded_url.save()
        if embedded_url and embedded_url.html:
            return embedded_url.html
    context = {'url': url, 'external_task': external_task}
    return render_to_string('richtext/_external_link.html', context)


@register.filter
@stringfilter
def embed(html):
    """Finds Slideshare [slideshare: ...] tags, and replace them
    with an embeddable HTML snippet.
    """
    return '<div class="richtext_section">%s</div>' % re.sub(
        EMBED_RE, replace, html)

embed.is_safe = True  # Don't escape HTML
