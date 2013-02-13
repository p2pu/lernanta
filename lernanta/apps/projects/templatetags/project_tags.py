import datetime

from django import template
from django.db.models import Q
from django.contrib.sites.models import Site

from content.models import Page
from signups.models import Signup
from statuses import forms as statuses_forms
from activity.views import filter_activities
from pagination.views import get_pagination_context
from activity.models import apply_filter
from l10n.urlresolvers import reverse

from projects.models import Project, PerUserTaskCompletion
from projects import drupal
from badges.models import Badge
from schools.models import ProjectSet


register = template.Library()


def sidebar(context):
    user = context['user']
    project = context['project']
    sign_up = Signup.objects.get(project=project)
    is_participating = is_following = is_organizing = False
    if user.is_authenticated():
        is_participating = project.participants().filter(user=user).exists()
        profile = user.get_profile()
        is_following = profile.is_following(project)
        is_organizing = project.organizers().filter(user=user).exists()

    tags = project.tags.exclude(slug='').order_by('name')

    organizers = project.organizers()
    organizers_count = organizers.count()
    participants = project.non_organizer_participants()
    participants_count = participants.count()
    followers = project.non_participant_followers()
    followers_count = followers.count()

    update_count = project.activities().count()
    pending_signup_answers_count = sign_up.pending_answers().count()
    content_pages = Page.objects.filter(project__pk=project.pk,
        listed=True, deleted=False).order_by('index')
    links = project.link_set.all().order_by('index')
    school = project.accepted_school()
    imported_from = None
    if project.imported_from:
        imported_from = drupal.get_course(project.imported_from)

    can_add_task = is_organizing
    if project.category == Project.STUDY_GROUP:
        can_add_task = is_participating
    can_change_order = can_add_task

    chat = '#p2pu-%s-%s' % (project.id, project.slug[:10])

    submission_enabled_badges = project.get_submission_enabled_badges()

    context.update({
        'participating': is_participating,
        'participants_count': participants_count,
        'following': is_following,
        'followers_count': followers_count,
        'tags': tags,
        'organizing': is_organizing,
        'organizers_count': organizers_count,
        'update_count': update_count,
        'pending_signup_answers_count': pending_signup_answers_count,
        'content_pages': content_pages,
        'links': links,
        'school': school,
        'imported_from': imported_from,
        'sign_up': sign_up,
        'can_add_task': can_add_task,
        'can_change_order': can_change_order,
        'chat': chat,
        'discussion_area': context.get('discussion_area', False),
        'is_challenge': (project.category == Project.CHALLENGE),
        'submission_enabled_badges': submission_enabled_badges,
    })
    return context

register.inclusion_tag('projects/sidebar.html', takes_context=True)(sidebar)


def task_list(project, user, show_all_tasks=True, short_list_length=3):
    tasks = Page.objects.filter(project=project, listed=True,
        deleted=False).order_by('index')
    tasks_count = visible_count = tasks.count()
    if not show_all_tasks:
        tasks = tasks[:short_list_length]
        visible_count = tasks.count()
    is_challenge = (project.category == Project.CHALLENGE)
    is_participating = is_organizing = adopter = False
    completed_count = 0
    if is_challenge and user.is_authenticated():
        profile = user.get_profile()
        is_organizing = project.organizers().filter(user=profile).exists()
        is_participating = project.participants().filter(user=profile).exists()
        if is_participating:
            for task in tasks:
                task.is_done = PerUserTaskCompletion.objects.filter(
                    user=profile, page=task, unchecked_on__isnull=True)
        completed_count = PerUserTaskCompletion.objects.filter(
            page__project=project, page__deleted=False,
            unchecked_on__isnull=True, user=profile).count()
    progressbar_value = 0
    if tasks_count:
        progressbar_value = (completed_count * 100 / tasks_count)
    return {
        'project': project,
        'user': user,
        'tasks': tasks,
        'tasks_count': tasks_count,
        'visible_count': visible_count,
        'show_all': show_all_tasks,
        'is_challenge': is_challenge,
        'participating': is_participating,
        'organizing': is_organizing,
        'completed_count': completed_count,
        'progressbar_value': progressbar_value,
    }

register.inclusion_tag('projects/_task_list.html')(task_list)


def tasks_completed_msg(project, user, start_hidden=True,
        adopter_request=True):
    awarded_non_completion_badges = project.get_awarded_badges(
        user, exclude_completion_badges=True)
    awarded_completion_badges = project.get_upon_completion_badges(
        user)
    # Manually include self+completed badges so they are in the awarded badges
    # list that is displayed when all tasks are completed (even if the django
    # post save signal that awards those badges has not run yet).
    awarded_badges = Badge.objects.filter(
        Q(id__in=awarded_non_completion_badges.values('id'))
        | Q(id__in=awarded_completion_badges.values('id')))
    badges_in_progress = project.get_badges_in_progress(user)
    non_attempted_badges = project.get_non_attempted_badges(user)
    non_started_challenges = project.get_non_started_next_projects(
        user)
    next_challenges = project.next_projects.all()
    return {
        'project': project,
        'start_hidden': start_hidden,
        'awarded_badges': awarded_badges,
        'badges_in_progress': badges_in_progress,
        'non_attempted_badges': non_attempted_badges,
        'non_started_challenges': non_started_challenges,
        'adopter_request': adopter_request,
        'next_challenges': next_challenges,
    }

register.inclusion_tag('projects/_tasks_completed_msg.html')(
    tasks_completed_msg)


def project_wall(request, project, discussion_area=False):
    is_organizing = project.is_organizing(request.user)
    is_participating = project.is_participating(request.user)
    if is_organizing:
        form = statuses_forms.ImportantStatusForm()
    elif is_participating:
        form = statuses_forms.StatusForm()
    else:
        form = None

    activities = project.activities()
    if discussion_area:
        activities = apply_filter(activities, 'messages')
    else:
        activities = filter_activities(request, activities)
    is_challenge = (project.category == Project.CHALLENGE)
    if is_challenge:
        url = reverse('projects_discussion_area',
            kwargs=dict(slug=project.slug))
    else:
        url = project.get_absolute_url()

    context = {
        'request': request,
        'user': request.user,
        'project': project,
        'participating': is_participating,
        'organizing': is_organizing,
        'form': form,
        'discussion_area': discussion_area,
        'domain': Site.objects.get_current().domain,
        'wall_url': url,
        'is_challenge': is_challenge,
    }
    context.update(get_pagination_context(request, activities))
    return context

register.inclusion_tag('projects/_wall.html')(project_wall)


def tasks_list_wall(request, project, user, toggled_tasks=True):
    tasks = Page.objects.filter(project=project, listed=True,
        deleted=False).order_by('index')
    tasks_count = tasks.count()
    is_participating = is_organizing = adopter = False
    completed_count = 0
    if user.is_authenticated():
        profile = user.get_profile()
        is_organizing = project.organizers().filter(user=profile).exists()
        adopter = project.adopters().filter(user=profile).exists()
        is_participating = project.participants().filter(user=profile).exists()
        completed_count = PerUserTaskCompletion.objects.filter(
            page__project=project, page__deleted=False,
            unchecked_on__isnull=True, user=profile).count()
    progressbar_value = 0
    if tasks_count:
        progressbar_value = (completed_count * 100 / tasks_count)
    hidde_tasks_complete_msg = (progressbar_value != 100)
    adopter_request = (not is_organizing and not adopter)
    next_projects = project.next_projects.all()
    next_badges = project.get_badges().order_by('id')
    context = {
        'tasks_count': tasks_count,
        'completed_count': completed_count,
        'progressbar_value': progressbar_value,
        'participating': is_participating,
        'request': request,
        'project': project,
        'user': user,
        'toggled_tasks': toggled_tasks,
        'discussion_area': True,
        'adopter_request': adopter_request,
        'hidde_tasks_complete_msg': hidde_tasks_complete_msg,
        'next_projects': next_projects,
        'next_badges': next_badges,
    }
    return context

register.inclusion_tag('projects/_tasks_list_wall.html')(tasks_list_wall)


def project_user_list(request, project, max_count=64, with_sections=False,
        paginate_sections=False, user_list_url=''):
    is_challenge = (project.category == Project.CHALLENGE)
    context = {
        'request': request,
        'project': project,
        'user_list_url': user_list_url,
        'with_sections': with_sections,
        'paginate_sections': paginate_sections,
        'is_challenge': is_challenge,
    }
    if is_challenge:
        organizers = project.adopters().order_by('-organizing', '-id')
        participants = project.non_adopter_participants().order_by('-id')
        followers = project.non_participant_followers()
    else:
        organizers = project.organizers()
        participants = project.non_organizer_participants()
        followers = project.non_participant_followers()

    if with_sections:
        per_section_max_count = max_count / 3
        if paginate_sections:
            context.update(get_pagination_context(request, organizers,
                per_section_max_count, prefix='organizers_'))
            context.update(get_pagination_context(request, participants,
                per_section_max_count, prefix='participants_'))
            context.update(get_pagination_context(request, followers,
                per_section_max_count, prefix='followers_'))
            context['organizers'] = context[
                'organizers_pagination_current_page'].object_list
            context['participants'] = context[
                'participants_pagination_current_page'].object_list
            context['followers'] = context[
                'followers_pagination_current_page'].object_list
        else:
            context['organizers'] = organizers[:per_section_max_count]
            context['participants'] = participants[:per_section_max_count]
            context['followers'] = followers[:per_section_max_count]
            show_more_link = (organizers.count() > per_section_max_count)
            show_more_link = show_more_link or (
                participants.count() > per_section_max_count)
            show_more_link = show_more_link or (
                followers.count() > per_section_max_count)
            context['show_more_link'] = show_more_link
    else:
        remaining = max_count
        context['organizers'] = organizers[:remaining]
        remaining -= context['organizers'].count()
        if remaining > 0:
            context['participants'] = participants[:remaining]
            remaining -= context['participants'].count()
        if remaining > 0:
            context['followers'] = followers[:remaining]
            remaining -= context['followers'].count()
        # It could be equal to (remaining < 0) but the big user
        # list page is not a has more information than the sidebar
        # section.
        context['show_more_link'] = True
    return context

register.inclusion_tag('projects/_user_list.html')(project_user_list)
