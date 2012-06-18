from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django import http
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from l10n.urlresolvers import reverse
from users.decorators import login_required
from drumbeat import messages
from pagination.views import get_pagination_context
from projects.models import Project

from activity.models import Activity, apply_filter


def filter_activities(request, activities, default=None):
    if 'activities_filter' in request.GET:
        filter_name = request.GET['activities_filter']
        return apply_filter(activities, filter_name)
    return apply_filter(activities, 'default')


def index(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    context = {
        'activity': activity,
        'domain': Site.objects.get_current().domain,
    }
    if activity.scope_object:
        scope_url = activity.scope_object.get_absolute_url()
        context['project'] = activity.scope_object
    else:
        scope_url = activity.actor.get_absolute_url()
        context['profile'] = activity.actor
        context['profile_view'] = True
    if activity.deleted:
        messages.error(request, _('This activity was deleted.'))
        if activity.can_edit(request.user):
            return http.HttpResponseRedirect(reverse('activity_restore',
                kwargs={'activity_id': activity.id}))
        return http.HttpResponseRedirect(scope_url)
    replies = activity.first_level_comments()
    context.update(get_pagination_context(request, replies))
    return render_to_response('activity/index.html', context,
        context_instance=RequestContext(request))


@login_required
def delete_restore(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if activity.scope_object:
        if activity.scope_object.deleted:
            raise http.Http404
    if not activity.can_edit(request.user):
        return http.HttpResponseForbidden(_("You can't edit this activity"))
    if request.method == 'POST':
        activity.deleted = not activity.deleted
        activity.save()
        if activity.deleted:
            msg = _('Activity deleted!')
        else:
            msg = _('Activity restored!')
        messages.success(request, msg)
        if activity.scope_object:
            return http.HttpResponseRedirect(
                activity.scope_object.get_absolute_url())
        else:
            return http.HttpResponseRedirect(reverse('dashboard'))
    else:
        return render_to_response('activity/delete_restore.html', {
            'activity': activity,
        }, context_instance=RequestContext(request))
