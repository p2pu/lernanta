import unicodecsv
import logging
import sys

from django.conf import settings
from django import http
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from l10n.urlresolvers import reverse
from users.models import UserProfile
from notifications.models import send_notifications
from drumbeat.forms import AbuseForm
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
    """Make MEDIA_URL available to the 500 template."""
    t = loader.get_template('500.html')
    return http.HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL,
    })))


def report_abuse(request, model, app_label, pk):
    """Report abusive or irrelavent content."""
    if request.method == 'POST':
        # we only use the form for the csrf middleware. skip validation.
        form = AbuseForm(request.POST)
        content_type_cls = get_object_or_404(ContentType, model=model,
            app_label=app_label).model_class()
        instance = get_object_or_404(content_type_cls, pk=pk)
        try:
            url = request.build_absolute_uri(instance.get_absolute_url())
        except NoReverseMatch:
            url = request.build_absolute_uri(reverse('dashboard'))
        subject_template = 'drumbeat/emails/abuse_report_subject.txt'
        body_template = 'drumbeat/emails/abuse_report.txt'
        context = {
            'user': request.user.get_profile(),
            'url': url, 'model': model,
            'app_label': app_label, 'pk': pk,
        }
        try:
            profile = UserProfile.objects.get(email=settings.ADMINS[0][1])
            send_notifications([profile], subject_template, body_template, context)
        except:
            log.debug("Error sending abuse report: %s" % sys.exc_info()[0])
            pass
        return render_to_response('drumbeat/report_received.html', {},
                                  context_instance=RequestContext(request))
    else:
        form = AbuseForm()
    return render_to_response('drumbeat/report_abuse.html', {
        'form': form,
        'model': model,
        'app_label': app_label,
        'pk': pk,
    }, context_instance=RequestContext(request))


def export_as_csv(modeladmin, request, queryset):
    """
    Generic csv export admin action.
    """
    if not request.user.is_staff:
        raise PermissionDenied
    opts = modeladmin.model._meta
    response = HttpResponse(mimetype='text/csv')
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
