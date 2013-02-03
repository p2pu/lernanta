import logging

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse
from statuses.forms import StatusForm, ImportantStatusForm
from projects.models import Project
from users.decorators import login_required

from drumbeat import messages

log = logging.getLogger(__name__)


@login_required
def create(request):
    messages.error(request, _('Posting a update to your dashboard is no longer supported'))
    return HttpResponseRedirect(reverse('dashboard'))
    #if request.method != 'POST' or 'status' not in request.POST:
    #    return HttpResponseRedirect(reverse('dashboard'))
    #form = StatusForm(data=request.POST)
    #if form.is_valid() and len( request.user.get_profile().can_post() )>0:
    #    status = form.save(commit=False)
    #    status.author = request.user.get_profile()
    #    status.save()
    #else:
    #    log.debug("form error: %s" % (str(form.errors)))
    #    messages.error(request, _('There was an error posting '
    #                              'your status update'))
    #return HttpResponseRedirect(reverse('dashboard'))


@login_required
def create_project_status(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.category == Project.CHALLENGE:
        url = reverse('projects_discussion_area',
            kwargs=dict(slug=project.slug))
    else:
        url = project.get_absolute_url()
    if request.method != 'POST' or 'status' not in request.POST:
        return HttpResponseRedirect(url)
    if not project.is_participating(request.user):
        return HttpResponseRedirect(url)
    if project.is_organizing(request.user):
        form = ImportantStatusForm(data=request.POST)
    else:
        form = StatusForm(data=request.POST)
    if form.is_valid():
        status = form.save(commit=False)
        status.author = request.user.get_profile()
        status.project = project
        status.save()
        log.debug("Saved status by user (%d) to study group (%d): %s" % (
        status.author.id, project.id, status))
    else:
        log.debug("form error: %s" % (str(form.errors)))
        messages.error(request, _('There was an error posting '
                                  'your status update'))
    return HttpResponseRedirect(url)
