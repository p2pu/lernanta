import logging

from django import http
from django.template import RequestContext, Context
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse
from users.decorators import login_required
from abuse.models import send_abuse_report
from abuse.forms import AbuseForm, AbuseReasonForm
from drumbeat import messages

log = logging.getLogger(__name__)


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
        return render_to_response('abuse/report_received.html', {},
                                  context_instance=RequestContext(request))
    else:
        form = AbuseForm()
    return render_to_response('abuse/report_abuse.html', {
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
    return render_to_response('abuse/abuse_reason.html',
        context,
        context_instance=RequestContext(request))
