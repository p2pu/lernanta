from django import template

from badges.models import get_awarded_badges
from projects import drupal as projects_drupal
from links.models import Link
from badges.models import Badge, Award

register = template.Library()


def user_sidebar(context, max_people_count=64):
    profile = context['profile']
    profile_view = context['profile_view']

    current_projects = profile.get_current_projects(only_public=profile_view)
    users_following = profile.following()
    users_followers = profile.followers()

    interests = profile.tags.filter(category='interest').exclude(
        slug='').order_by('name')
    desired_topics = profile.tags.exclude(slug='').filter(
        category='desired_topic').order_by('name')

    links = Link.objects.filter(user=profile,
        project__isnull=True).order_by('index')

    # only display non actionable items on the profile.
    skills = past_projects = past_drupal_courses = badges = pilot_badges = []
    past_involvement_count = badges_count = 0
    if profile_view:
        skills = profile.tags.filter(category='skill').exclude(
            slug='').order_by('name')
        past_projects = profile.get_past_projects(only_public=profile_view)
        past_drupal_courses = projects_drupal.get_past_courses(
            profile.username)
        past_involvement_count = len(past_projects) + len(past_drupal_courses)
        pilot_badges = get_awarded_badges(profile.user).values()
        badge_awards = Award.objects.filter(
            user=profile).values('badge_id')
        badges = Badge.objects.filter(id__in=badge_awards)
        badges_count = len(pilot_badges) + badges.count()

    context.update({
        'current_projects': current_projects,
        'users_following': users_following,
        'users_followers': users_followers,
        'skills': skills,
        'interests': interests,
        'desired_topics': desired_topics,
        'links': links,
        'past_projects': past_projects,
        'past_drupal_courses': past_drupal_courses,
        'past_involvement_count': past_involvement_count,
        'badges': badges,
        'pilot_badges': pilot_badges,
        'badges_count': badges_count,
    })
    return context

register.inclusion_tag('users/sidebar.html', takes_context=True)(user_sidebar)


def group_list(context, limit=None):
    profile = context['profile']
    profile_view = context['profile_view']
    current_projects = profile.get_current_projects(only_public=profile_view)

    organizing = current_projects['organizing']
    participating = current_projects['participating']
    following = current_projects['following']

    if limit:
        organizing = organizing[:limit]
        participating = participating[:limit]
        following = following[:limit]

    context.update({
        'organizing': organizing,
        'participating': participating,
        'following': following, })
    return context

register.inclusion_tag('users/_groups.html', takes_context=True)(group_list)
