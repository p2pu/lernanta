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

from l10n.urlresolvers import reverse
from users.models import UserProfile
from users.decorators import login_required
from notifications.models import send_notifications
from drumbeat.models import send_abuse_report
from drumbeat.forms import AbuseForm, AbuseReasonForm
from drumbeat import messages
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


@login_required
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

        reason = "abusive"
        other = "model: {}, app_label: {}, pk: {}".format(model, app_label, pk)
        send_abuse_report(url, reason, other, request.user.get_profile())
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


@login_required
def prompt_abuse_reason(request):
    form = AbuseReasonForm(request.POST)
    if form.is_valid():
        # report abuse
        abuse_url = form.cleaned_data.get('url')
        reason = form.cleaned_data.get('reason')
        other = form.cleaned_data.get('other')
        send_abuse_report(abuse_url, reason, other, request.user.get_profile())
        messages.success(request, _("Thank you for filing an abuse report!"))
        return http.HttpResponseRedirect(abuse_url)

    context = { 'form': form }
    return render_to_response('drumbeat/abuse_reason.html',
        context,
        context_instance=RequestContext(request))


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
