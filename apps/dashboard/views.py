import random

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from django.views.decorators.csrf import csrf_exempt

from l10n.urlresolvers import reverse
from activity.models import Activity
from users.decorators import anonymous_only, login_required
from users.models import UserProfile
from users.forms import CreateProfileForm
from projects.models import Project
from dashboard.models import FeedEntry
from relationships.models import Relationship


@anonymous_only
def splash(request):
    """Splash page we show to users who are not authenticated."""
    project = None
    projects = Project.objects.filter(featured=True)
    if projects:
        project = random.choice(projects)
        project.followers_count = Relationship.objects.filter(
            target_project=project).count()
    activities = Activity.objects.public()
    feed_entries = FeedEntry.objects.all().order_by('-created_on')[0:4]
    feed_url = getattr(settings, 'SPLASH_PAGE_FEED', None)
    return render_to_response('dashboard/splash.html', {
        'activities': activities,
        'featured_project': project,
        'feed_entries': feed_entries,
        'feed_url': feed_url,
    }, context_instance=RequestContext(request))


@login_required
@csrf_exempt
def hide_welcome(request):
    profile = request.user.get_profile()
    if not profile.discard_welcome:
        profile.discard_welcome = True
        profile.save()
    if request.is_ajax():
        return HttpResponse()
    return HttpResponseRedirect(reverse('dashboard_index'))


@login_required(profile_required=False)
def dashboard(request):
    """Personalized dashboard for authenticated users."""
    try:
        profile = request.user.get_profile()
    except UserProfile.DoesNotExist:
        user = request.user
        username = ''
        if user.username[:10] != 'openiduser':
            username = user.username
        form = CreateProfileForm(initial={
            'full_name': ' '.join((user.first_name, user.last_name)),
            'email': user.email,
            'username': username,
        })
        return render_to_response('dashboard/setup_profile.html', {
            'form': form,
        }, context_instance=RequestContext(request))
    if profile.preflang and any(profile.preflang in l for l in settings.SUPPORTED_LANGUAGES):
        if (get_language() <> profile.preflang):
            activate(profile.preflang);
            return HttpResponseRedirect("/" + profile.preflang + "/")
    projects = profile.following(model=Project)
    projects_organizing = []
    projects_participating = []
    projects_following = []
    for project in projects:
        if project.is_organizing(request.user):
            project.relation_text = _('(organizing)')
            projects_organizing.append(project)
        elif project.is_participating(request.user):
            project.relation_text = _('(participating)')
            projects_participating.append(project)
        else:
            project.relation_text = _('(following)')
            projects_following.append(project)
    users_following = profile.following()
    users_followers = profile.followers()
    activities = Activity.objects.dashboard(request.user.get_profile())
    show_welcome = not profile.discard_welcome
    return render_to_response('dashboard/dashboard.html', {
        'projects': projects,
        'projects_following': projects_following,
        'projects_participating': projects_participating,
        'projects_organizing': projects_organizing,
        'users_following': users_following,
        'users_followers': users_followers,
        'activities': activities,
        'show_welcome': show_welcome,
    }, context_instance=RequestContext(request))


def index(request):
    """
    Direct user to personalized dashboard or generic splash page, depending
    on whether they are logged in authenticated or not.
    """
    if request.user.is_authenticated():
        return dashboard(request)
    return splash(request)
