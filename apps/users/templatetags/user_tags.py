from django import template

from users import badges
from projects import drupal as projects_drupal
from links.models import Link

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
    skills = past_projects = past_drupal_courses = pilot_badges = []
    past_involvement_count = 0
    if profile_view:
        skills = profile.tags.filter(category='skill').exclude(
            slug='').order_by('name')
        past_projects = profile.get_past_projects(only_public=profile_view)
        past_drupal_courses = projects_drupal.get_past_courses(
            profile.username)
        past_involvement_count = len(past_projects) + len(past_drupal_courses)
        pilot_badges = badges.get_awarded_badges(profile.username).values()

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
        'pilot_badges': pilot_badges,
    })
    return context

register.inclusion_tag('users/sidebar.html', takes_context=True)(user_sidebar)
