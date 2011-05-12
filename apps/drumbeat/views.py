from django.conf import settings
from django import http
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import ugettext_lazy as _

from l10n.urlresolvers import reverse
from users.models import UserProfile
from users.tasks import SendUserEmail
from drumbeat.forms import AbuseForm

import logging
import sys

log = logging.getLogger(__name__)

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
        content_type_cls = get_object_or_404(ContentType, model=model, app_label=app_label).model_class()
        instance = get_object_or_404(content_type_cls, pk=pk)
        try:
            url = request.build_absolute_uri(instance.get_absolute_url())
        except NoReverseMatch:
            url = request.build_absolute_uri(reverse('dashboard_index'))
        body = _("""
        User %(display_name)s has reported the following content as objectionable:

        %(url)s
        
        (model: %(model)s, app_label: %(app_label)s, pk: %(pk)s)
        """ % dict(display_name = request.user.get_profile().display_name, 
            url = url, model = model, app_label = app_label, pk = pk))
        subject = _("Abuse Report")
        try:
            profile = UserProfile.objects.get(email=settings.ADMINS[0][1])
            SendUserEmail.apply_async(args=(profile, subject, body))
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


def journalism(request):
    return render_to_response('drumbeat/journalism.html', {

    }, context_instance=RequestContext(request))
