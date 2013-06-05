import unicodecsv
import logging

from django.conf import settings
from django import http
from django.template import RequestContext, Context, loader
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied

import django.contrib.sites as sites

log = logging.getLogger(__name__)


def page_not_found(request):
    """Render custom 404 page."""
    # Assume sites framework is enabled.
    domain = sites.models.Site.objects.get_current().domain
    domain = "http://%s" % domain
    d = dict(language=settings.LANGUAGE_CODE,
             domain=domain)

    return http.HttpResponseNotFound(
        loader.render_to_string('404.html', d,
        context_instance=RequestContext(request)) )


def server_error(request):
    """Make MEDIA_URL and STATIC_URL available to the 500 template."""
    t = loader.get_template('500.html')
    return http.HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
    })))


def export_as_csv(modeladmin, request, queryset):
    """
    Generic csv export admin action.
    """
    if not request.user.is_staff:
        raise PermissionDenied
    opts = modeladmin.model._meta
    response = http.HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(
        opts).replace('.', '_')
    writer = unicodecsv.writer(response, encoding='utf-8')
    field_names = [field.name for field in opts.fields]
    # Write a first row with header information
    writer.writerow(field_names)
    # Write data rows
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response
export_as_csv.short_description = _("Export selected objects as csv file")
