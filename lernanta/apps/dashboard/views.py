import random

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse
from activity.models import Activity
from users.decorators import login_required
from users.models import UserProfile
from users.forms import CreateProfileForm
from projects.models import Project
from news.models import FeedEntry
from drumbeat import messages
from activity.views import filter_activities
from pagination.views import get_pagination_context
from tracker import models as tracker_models
from links.models import Link
from learn.models import get_courses_by_list


def splash(request):
    """Splash page we show to users who are not authenticated."""
    courses = get_courses_by_list("community")
    featured_count = min(4,len(courses))
    courses = random.sample(courses, featured_count)
    activities = Activity.objects.public()
    feed_entries = FeedEntry.objects.filter(
        page='splash').order_by('-created_on')[0:4]
    feed_url = settings.FEED_URLS['splash']
    context = {
        'activities': activities,
        'featured_projects': courses,
        'feed_entries': feed_entries,
        'feed_url': feed_url,
        'domain': Site.objects.get_current().domain,
    }
    context.update(tracker_models.get_google_tracking_context())
    return render_to_response('dashboard/splash.html',
        context, context_instance=RequestContext(request))


@login_required
@csrf_exempt
def hide_welcome(request):
    profile = request.user.get_profile()
    if not profile.discard_welcome:
        profile.discard_welcome = True
        profile.save()
    if request.is_ajax():
        return HttpResponse()
    return HttpResponseRedirect(reverse('dashboard'))


@login_required(profile_required=False)
def dashboard(request):
    """Personalized dashboard for authenticated users."""
    try:
        profile = request.user.get_profile()
        return HttpResponseRedirect(reverse("users_profile_view", kwargs={"username": request.user.username}))
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
        messages.info(request,
            _('Please fill out your profile to finish registration.'))
        return render_to_response('dashboard/setup_profile.html', {
            'form': form,
        }, context_instance=RequestContext(request))
    show_welcome = not profile.discard_welcome
    activities = Activity.objects.dashboard(
        request.user.get_profile())
    activities = filter_activities(request, activities)
    context = {
        'profile': profile,
        'current_projects': current_projects,
        'users_following': users_following,
        'users_followers': users_followers,
        'interests': interests,
        'desired_topics': desired_topics,
        'links': links,
        'show_welcome': show_welcome,
        'domain': Site.objects.get_current().domain,
        'dashboard_url': reverse('dashboard'),
    }
    context.update(get_pagination_context(request, activities))
    return render_to_response('dashboard/dashboard.html', context,
        context_instance=RequestContext(request))
