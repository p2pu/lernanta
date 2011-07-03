import datetime

from django import template

from content.models import Page
from projects.models import Project
from projects import drupal


register = template.Library()


def sidebar(context):
    max_participants = 64
    user = context['user']
    project = context['project']
    is_participating = is_following = is_organizing = False
    pending_signup = None
    if user.is_authenticated():
        is_participating = project.participants().filter(user=user).exists()
        profile = user.get_profile()
        is_following = profile.is_following(project)
        is_organizing = project.organizers().filter(user=user).exists()
        if not is_participating and not is_organizing:
            signup = Page.objects.get(slug='sign-up', project=project)
            answers = signup.comments.filter(reply_to__isnull=True,
                deleted=False, author=profile)
            if answers.exists():
                pending_signup = answers[0]

    remaining = max_participants
    organizers = project.organizers()[:max_participants]
    participants = []
    followers = []
    remaining -= len(organizers)
    if remaining > 0:
        participants = project.non_organizer_participants()[:remaining]
        remaining -= len(participants)
    if remaining > 0:
        followers = project.non_participant_followers()[:remaining]
        remaining -= len(followers)

    participants_count = project.non_organizer_participants().count()
    followers_count = project.non_participant_followers().count()
    organizers_count = project.organizers().count()
    update_count = project.activities().count()
    pending_applicants_count = len(project.pending_applicants())
    content_pages = Page.objects.filter(project__pk=project.pk,
        listed=True, deleted=False).order_by('index')
    links = project.link_set.all().order_by('index')
    school = project.accepted_school()
    imported_from = None
    if project.imported_from:
        imported_from = drupal.get_course(project.imported_from)
    context.update({
        'participating': is_participating,
        'participants_count': participants_count,
        'following': is_following,
        'followers_count': followers_count,
        'organizing': is_organizing,
        'organizers_count': organizers_count,
        'update_count': update_count,
        'pending_applicants_count': pending_applicants_count,
        'content_pages': content_pages,
        'links': links,
        'school': school,
        'imported_from': imported_from,
        'pending_signup': pending_signup,
        'sidebar_organizers': organizers,
        'sidebar_participants': participants,
        'sidebar_followers': followers,
    })
    return context

register.inclusion_tag('projects/sidebar.html', takes_context=True)(sidebar)


def project_list(school=None, limit=8):
    listed = Project.objects.filter(under_development=False, not_listed=False,
        archived=False)
    if school:
        featured = school.featured.filter(not_listed=False, archived=False)
    else:
        featured = listed.filter(featured=True)
    active = Project.objects.get_active(limit=limit, school=school)
    popular = Project.objects.get_popular(limit=limit, school=school)
    one_week = datetime.datetime.now() - datetime.timedelta(weeks=1)
    new = listed.filter(created_on__gte=one_week).order_by('-created_on')
    open_signup = listed.filter(signup_closed=False)
    under_development = Project.objects.filter(under_development=True,
        not_listed=False, archived=False)
    archived = Project.objects.filter(not_listed=False,
        archived=True).order_by('-created_on')
    if school:
        featured = featured.filter(school=school).exclude(
            id__in=school.declined.values('id'))
        new = new.filter(school=school).exclude(
            id__in=school.declined.values('id'))
        open_signup = open_signup.filter(school=school).exclude(
            id__in=school.declined.values('id'))
        under_development = under_development.filter(school=school).exclude(
            id__in=school.declined.values('id'))
        archived = archived.filter(school=school).exclude(
            id__in=school.declined.values('id'))
    if limit:
        new = new[:limit]
        archived = archived[:limit]
        under_development = under_development[:limit]
    return {'featured': featured, 'active': active, 'popular': popular,
        'new': new, 'open_signup': open_signup,
        'under_development': under_development,
        'archived': archived, 'school': school}

register.inclusion_tag('projects/_project_list.html')(project_list)
