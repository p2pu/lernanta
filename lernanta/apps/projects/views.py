import logging
import datetime
import unicodecsv
import itertools

from django import http
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import get_language, ugettext as _
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.db.models import Q, Count, Max
from django.contrib.contenttypes.models import ContentType

from commonware.decorators import xframe_sameorigin

# from links.tasks import UnsubscribeFromFeed
from pagination.views import get_pagination_context

from projects import forms as project_forms
from projects.decorators import organizer_required, participation_required
from projects.decorators import can_view_metric_overview, can_view_metric_detail
from projects.decorators import restrict_project_kind, hide_deleted_projects
from projects.models import Project, Participation, PerUserTaskCompletion
from projects import drupal

from l10n.urlresolvers import reverse
from relationships.models import Relationship
from links.models import Link
from users.models import UserProfile
from content.models import Page
from content.templatetags.content_tags import task_toggle_completion
from schools.models import School
from activity.models import Activity, RemoteObject
from activity.schema import verbs
from signups.models import Signup
from tracker import models as tracker_models
from reviews.models import Review
from utils import json_date_encoder

from drumbeat import messages
from users.decorators import login_required

log = logging.getLogger(__name__)


def learn(request, max_count=24):
    projects = Project.objects.filter(not_listed=False,
        deleted=False).order_by('-created_on')
    get_params = request.GET.copy()
    if not 'language' in get_params:
        get_params['language'] = get_language()
    form = project_forms.ProjectsFilterForm(projects, get_params)
    context = {
        'schools': School.objects.all(),
        'popular_tags': Project.get_popular_tags(),
        'form': form,
        'learn_url': reverse('projects_learn'),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
    }
    if form.is_valid():
        archived = form.cleaned_data['archived']
        under_development = form.cleaned_data['under_development']
        projects = projects.filter(archived=archived,
            under_development=under_development)
        closed_signup = form.cleaned_data['closed_signup']
        if closed_signup:
            projects = projects.exclude(
                category=Project.CHALLENGE).filter(
                sign_up__status=Signup.CLOSED)
        else:
            projects = projects.filter(Q(category=Project.CHALLENGE)
                | Q(sign_up__status=Signup.MODERATED)
                | Q(sign_up__status=Signup.NON_MODERATED))
        featured = form.cleaned_data['featured']
        if featured == project_forms.ProjectsFilterForm.SHOWCASE:
            context['learn_showcase'] = True
            projects = projects.filter(featured=True)
        elif featured == project_forms.ProjectsFilterForm.COMMUNITY:
            context['learn_community'] = True
            projects = projects.filter(community_featured=True)
        elif featured == project_forms.ProjectsFilterForm.FRESH:
            context['learn_fresh'] = True
            one_week = datetime.datetime.now() - datetime.timedelta(weeks=1)
            projects = projects.filter(created_on__gte=one_week)
        elif featured == project_forms.ProjectsFilterForm.POPULAR:
            popular = Relationship.objects.filter(
                deleted=False, target_project__isnull=False).values(
                'target_project').annotate(Count('source')).order_by(
                '-source__count')[:max_count]
            popular_ids = [d['target_project'] for d in popular]
            projects = projects.filter(id__in=popular_ids)
        elif featured == project_forms.ProjectsFilterForm.UPDATED:
            external_ct = ContentType.objects.get_for_model(RemoteObject)
            relationship_ct = ContentType.objects.get_for_model(Relationship)
            last_updated = Activity.objects.filter(
                deleted=False, scope_object__isnull=False).exclude(
                target_content_type=external_ct).exclude(
                target_content_type=relationship_ct).values(
                'scope_object').annotate(Max('created_on')).order_by(
                '-created_on__max')[:max_count]
            last_updated_ids = [d['scope_object'] for d in last_updated]
            projects = projects.filter(id__in=last_updated_ids)
        school = form.cleaned_data['school']
        if school:
            context['learn_school'] = school
            projects = projects.filter(school=school)
        tag = form.cleaned_data['tag']
        if tag:
            context['learn_tag'] = tag
            projects = Project.get_tagged_projects(tag, projects)
        if not form.cleaned_data['all_languages']:
            language = form.cleaned_data['language']
            projects = projects.filter(language__startswith=language)
        reviewed = form.cleaned_data['reviewed']
        if reviewed:
            accepted_reviews = Review.objects.filter(
                accepted=True).values('project_id')
            projects = projects.filter(id__in=accepted_reviews)
    context['projects'] = projects
    context.update(get_pagination_context(request, projects, max_count))
    if request.is_ajax():
        projects_html = render_to_string('projects/_learn_projects.html',
            context, context_instance=RequestContext(request))
        projects_pagination = render_to_string('projects/_learn_pagination.html',
            context, context_instance=RequestContext(request))
        learn_header = render_to_string('projects/_learn_header.html',
            context, context_instance=RequestContext(request))
        learn_filters = render_to_string('projects/_learn_filters.html',
            context, context_instance=RequestContext(request))
        data = {
            'projects_html': projects_html,
            'projects_pagination': projects_pagination,
            'learn_header': learn_header,
            'learn_filters': learn_filters,
        }
        json = simplejson.dumps(data)
        return http.HttpResponse(json, mimetype="application/json")
    return render_to_response('projects/learn.html', context,
        context_instance=RequestContext(request))


def learn_tags(request):
    tags = Project.get_weighted_tags()
    return render_to_response('projects/learn_tags.html', {'tags': tags},
        context_instance=RequestContext(request))


@login_required
def create(request, category=None):
    user = request.user.get_profile()
    if request.method == 'POST':
        form = project_forms.ProjectForm(category, request.POST)
        image_form = None
        if form.is_valid():
            project = form.save()
            if category:
                project.category = category
            image_form = project_forms.ProjectImageForm(request.POST,
                request.FILES, instance=project)
            if image_form.is_valid():
                image_form.save()
            project.set_duration(form.cleaned_data['duration'] or 0)
            #CS - too much logic in view
            act = Activity(actor=user,
                verb=verbs['post'],
                scope_object=project,
                target_object=project)
            act.save()
            participation = Participation(project=project, user=user,
                organizing=True)
            participation.save()
            new_rel, created = Relationship.objects.get_or_create(source=user,
                target_project=project)
            new_rel.deleted = False
            new_rel.save()
            detailed_description_content = render_to_string(
                "projects/detailed_description_initial_content.html",
                {'project': project})
            detailed_description = Page(title=_('Full Description'),
                slug='full-description', content=detailed_description_content,
                listed=False, author_id=user.id, project_id=project.id)
            if project.category != Project.STUDY_GROUP:
                detailed_description.collaborative = False
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            sign_up = Signup(author_id=user.id, project_id=project.id)
            sign_up.save()
            project.create()
            messages.success(request,
                _('The %s has been created.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_create_tasks',
                kwargs={'slug': project.slug,}))
        else:
            msg = _("Problem creating the course")
            messages.error(request, msg)
    else:
        form = project_forms.ProjectForm(category, initial={'test':True})
        image_form = project_forms.ProjectImageForm()
    context = {
        'form': form,
        'image_form': image_form,
        'category': category,
        'is_challenge': (category == Project.CHALLENGE),
    }
    return render_to_response('projects/project_create_overview.html',
        context, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
def create_overview(request, slug):
    project = get_object_or_404(Project, slug=slug)
    is_challenge = (project.category == project.CHALLENGE)
    if request.method == 'POST':
        form = project_forms.ProjectForm(project.category, request.POST,
            instance=project)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('%s updated!') % project.kind.capitalize())
            return http.HttpResponseRedirect(
                reverse('projects_create_tasks',
                    kwargs=dict(slug=project.slug)))
    else:
        form = project_forms.ProjectForm(project.category, instance=project)
    metric_permissions = project.get_metrics_permissions(request.user)
    return render_to_response('projects/project_create_overview.html', {
        'form': form,
        'project': project,
        'school': project.school,
        'summary_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': is_challenge,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
def create_tasks(request, slug):
    project = get_object_or_404(Project, slug=slug)
    pages = project.pages.filter(deleted=False,listed=True).order_by('index')
    context = {
        'project': project,
        'tasks': pages
    }
    return render_to_response('projects/project_create_tasks.html', context,
        context_instance=RequestContext(request))


def create_review(request, slug):
    project = get_object_or_404(Project, slug=slug)
    context = {
        'project': project
    }
    return render_to_response('projects/project_create_review.html', context,
        context_instance=RequestContext(request))


@login_required
def matching_kinds(request):
    if len(request.GET['term']) == 0:
        matching_kinds = Project.objects.values_list('kind').distinct()
    else:
        matching_kinds = Project.objects.filter(
            kind__icontains=request.GET['term']).values_list('kind').distinct()
    json = simplejson.dumps([kind[0] for kind in matching_kinds])

    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
def show(request, slug, toggled_tasks=True):
    project = get_object_or_404(Project, slug=slug)
    is_organizing = project.is_organizing(request.user)
    is_challenge = (project.category == Project.CHALLENGE)

    context = {
        'project': project,
        'organizing': is_organizing,
        'show_all_tasks': is_challenge,
        'is_challenge': is_challenge,
        'toggled_tasks': toggled_tasks,
    }
    context.update(tracker_models.get_google_tracking_context(project))
    return render_to_response('projects/project.html', context,
        context_instance=RequestContext(request))


@login_required
def clone(request):
    user = request.user.get_profile()
    if request.method == 'POST':
        form = project_forms.CloneProjectForm(request.POST)
        if form.is_valid():
            base_project = form.cleaned_data['project']
            #CS - too much logic in view
            project = Project(name=base_project.name,
                category=base_project.category,
                other=base_project.other,
                other_description=base_project.other_description,
                short_description=base_project.short_description,
                long_description=base_project.long_description,
                clone_of=base_project)
            project.save()
            act = Activity(actor=user,
                verb=verbs['post'],
                scope_object=project,
                target_object=project)
            act.save()
            participation = Participation(project=project, user=user,
                organizing=True)
            participation.save()
            new_rel, created = Relationship.objects.get_or_create(source=user,
                target_project=project)
            new_rel.deleted = False
            new_rel.save()
            detailed_description = Page(title=_('Full Description'),
                slug='full-description',
                content=base_project.detailed_description.content,
                listed=False, author_id=user.id, project_id=project.id)
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            base_sign_up = base_project.sign_up.get()
            sign_up = Signup(public=base_sign_up.public,
                between_participants=base_sign_up.between_participants,
                author_id=user.id, project_id=project.id)
            sign_up.save()
            project.save()
            tasks = Page.objects.filter(project=base_project, listed=True,
                deleted=False).order_by('index')
            for task in tasks:
                new_task = Page(title=task.title, content=task.content,
                    author=user, project=project)
                new_task.save()
            links = Link.objects.filter(project=base_project).order_by('index')
            for link in links:
                new_link = Link(name=link.name, url=link.url, user=user,
                    project=project)
                new_link.save()
            project.create()
            messages.success(request,
                _('The %s has been cloned.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_create_tasks', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                _("There was a problem cloning the study group, course, ..."))
    else:
        form = project_forms.CloneProjectForm()
    return render_to_response('projects/project_clone.html', {
        'form': form, 'clone_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def matching_projects(request):
    if len(request.GET['term']) == 0:
        raise http.Http404

    matching_projects = Project.objects.filter(deleted=False,
        slug__icontains=request.GET['term'])
    json = simplejson.dumps([project.slug for project in matching_projects])

    return http.HttpResponse(json, mimetype="application/json")


@login_required
def import_from_old_site(request):
    user = request.user.get_profile()
    if request.method == 'POST':
        form = project_forms.ImportProjectForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            #CS - too much logic in view
            project = Project(name=course['name'], kind=course['kind'],
                short_description=course['short_description'],
                long_description=course['long_description'],
                imported_from=course['slug'])
            project.save()
            act = Activity(actor=user,
                verb=verbs['post'],
                scope_object=project,
                target_object=project)
            act.save()
            participation = Participation(project=project, user=user,
                organizing=True)
            participation.save()
            new_rel, created = Relationship.objects.get_or_create(source=user,
                target_project=project)
            new_rel.deleted = False
            new_rel.save()
            if course['detailed_description']:
                detailed_description_content = course['detailed_description']
            else:
                detailed_description_content = render_to_string(
                    "projects/detailed_description_initial_content.html",
                    {'project': project})
            detailed_description = Page(title=_('Full Description'),
                slug='full-description', content=detailed_description_content,
                listed=False, author_id=user.id, project_id=project.id)
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            sign_up = Signup(between_participants=course['sign_up'],
                author_id=user.id, project_id=project.id)
            sign_up.save()
            project.save()
            for title, content in course['tasks']:
                new_task = Page(title=title, content=content, author=user,
                    project=project)
                new_task.save()
            for name, url in course['links']:
                new_link = Link(name=name, url=url, user=user, project=project)
                new_link.save()
            project.create()
            messages.success(request,
                _('The %s has been imported.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            msg = _("Problem importing the study group, course, ...")
            messages.error(request, msg)
    else:
        form = project_forms.ImportProjectForm()
    return render_to_response('projects/project_import.html', {
        'form': form, 'import_tab': True},
        context_instance=RequestContext(request))


@login_required
def matching_courses(request):
    if len(request.GET['term']) == 0:
        raise http.Http404

    matching_nodes = drupal.get_matching_courses(term=request.GET['term'])
    json = simplejson.dumps(matching_nodes)

    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
@login_required
@organizer_required
def edit(request, slug):
    project = get_object_or_404(Project, slug=slug)
    is_challenge = (project.category == project.CHALLENGE)
    if request.method == 'POST':
        form = project_forms.ProjectForm(project.category, request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('%s updated!') % project.kind.capitalize())
            return http.HttpResponseRedirect(
                reverse('projects_edit', kwargs=dict(slug=project.slug)))
    else:
        form = project_forms.ProjectForm(project.category, instance=project)
    metric_permissions = project.get_metrics_permissions(request.user)
    return render_to_response('projects/project_edit_summary.html', {
        'form': form,
        'project': project,
        'school': project.school,
        'summary_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': is_challenge,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@xframe_sameorigin
@organizer_required
@require_http_methods(['POST'])
def edit_image_async(request, slug):
    project = get_object_or_404(Project, slug=slug)
    form = project_forms.ProjectImageForm(request.POST, request.FILES,
                                          instance=project)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.image.name,
        }))
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@hide_deleted_projects
@login_required
@organizer_required
def edit_image(request, slug):
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    if request.method == 'POST':
        form = project_forms.ProjectImageForm(request.POST, request.FILES,
                                              instance=project)
        if form.is_valid():
            messages.success(request, _('Image updated'))
            form.save()
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = project_forms.ProjectImageForm(instance=project)
    return render_to_response('projects/project_edit_image.html', {
        'project': project,
        'form': form,
        'image_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': (project.category == project.CHALLENGE),
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.STUDY_GROUP, Project.COURSE)
def edit_links(request, slug):
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    profile = request.user.get_profile()
    if request.method == 'POST':
        form = project_forms.ProjectLinksForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.project = project
            link.user = profile
            link.save()
            messages.success(request, _('Link added.'))
            return http.HttpResponseRedirect(
                reverse('projects_edit_links', kwargs=dict(slug=project.slug)))
        else:
            messages.error(request, _('There was an error adding your link.'))
    else:
        form = project_forms.ProjectLinksForm()
    links = Link.objects.select_related('subscription').filter(project=project)
    return render_to_response('projects/project_edit_links.html', {
        'project': project,
        'form': form,
        'links': links,
        'links_tab': True,
        'can_view_metric_overview': metric_permissions,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.STUDY_GROUP, Project.COURSE)
def edit_links_edit(request, slug, link):
    link = get_object_or_404(Link, id=link)
    form = project_forms.ProjectLinksForm(request.POST or None, instance=link)
    profile = get_object_or_404(UserProfile, user=request.user)
    project = get_object_or_404(Project, slug=slug)
    if link.project != project:
        return http.HttpResponseForbidden(_("You can't edit this link"))
    metric_permissions = project.get_metrics_permissions(request.user)
    if form.is_valid():
        if link.subscription:
            #UnsubscribeFromFeed.apply_async(args=(link,))
            link.subscription = None
            link.save()
        link = form.save(commit=False)
        link.user = profile
        link.project = project
        link.save()
        messages.success(request, _('Link updated.'))
        return http.HttpResponseRedirect(
            reverse('projects_edit_links', kwargs=dict(slug=project.slug)))
    else:
        form = project_forms.ProjectLinksForm(instance=link)
    return render_to_response('projects/project_edit_links_edit.html', {
        'project': project,
        'form': form,
        'link': link,
        'links_tab': True,
        'can_view_metric_overview': metric_permissions,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.STUDY_GROUP, Project.COURSE)
def edit_links_delete(request, slug, link):
    if request.method == 'POST':
        project = get_object_or_404(Project, slug=slug)
        link = get_object_or_404(Link, pk=link)
        if link.project != project:
            return http.HttpResponseForbidden(_("You can't edit this link"))
        link.delete()
        messages.success(request, _('The link was deleted'))
    return http.HttpResponseRedirect(
        reverse('projects_edit_links', kwargs=dict(slug=slug)))


@hide_deleted_projects
@login_required
@organizer_required
def edit_participants(request, slug):
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    if request.method == 'POST':
        form = project_forms.ProjectAddParticipantForm(project, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            organizing = form.cleaned_data['organizer']
            participation = Participation(project=project, user=user,
                organizing=organizing)
            participation.save()
            new_rel, created = Relationship.objects.get_or_create(
                source=user, target_project=project)
            new_rel.deleted = False
            new_rel.save()
            messages.success(request, _('Participant added.'))
            return http.HttpResponseRedirect(reverse(
                'projects_edit_participants',
                kwargs=dict(slug=project.slug)))
        else:
            messages.error(request,
                _('There was an error adding the participant.'))
    else:
        form = project_forms.ProjectAddParticipantForm(project)
    return render_to_response('projects/project_edit_participants.html', {
        'project': project,
        'form': form,
        'participations': project.participants().order_by('joined_on'),
        'participants_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': (project.category == project.CHALLENGE),
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
def matching_non_participants(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if len(request.GET['term']) == 0:
        raise http.Http404

    non_participants = UserProfile.objects.filter(deleted=False).exclude(
        id__in=project.participants().values('user_id'))
    matching_users = non_participants.filter(
        username__icontains=request.GET['term'])
    json = simplejson.dumps([user.username for user in matching_users])

    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
@login_required
@organizer_required
def edit_participants_make_organizer(request, slug, username):
    participation = get_object_or_404(Participation,
            project__slug=slug, user__username=username, left_on__isnull=True)
    if participation.organizing or request.method != 'POST':
        return http.HttpResponseForbidden(
            _("You can't make that person an organizer"))
    participation.left_on = datetime.datetime.now()
    participation.save()
    participation = Participation(user=participation.user, project=participation.project)
    participation.organizing = True
    participation.save()
    messages.success(request, _('The participant is now an organizer.'))
    return http.HttpResponseRedirect(reverse('projects_edit_participants',
        kwargs=dict(slug=participation.project.slug)))

@hide_deleted_projects
@login_required
@organizer_required
def edit_participants_organizer_delete(request, slug, username):
    """ remove username as an organizer for the course """
    project = get_object_or_404(Project, slug=slug)
    profile = get_object_or_404(UserProfile, username=username)
    participation = get_object_or_404(Participation, project=project,
        user=profile.user, left_on__isnull=True)
    organizers = project.organizers()
    # check that this isn't the only organizer
    if len(organizers) == 1:
        messages.error(request, _('You cannot delete the only organizer'))
    elif request.method != 'POST':
        raise http.Http404
    else:
        participation.left_on = datetime.datetime.now()
        participation.save()
        participation = Participation(user=profile, project=project)
        participation.save()
        messages.success(request, _('The organizer in now only a participant.'))
    return http.HttpResponseRedirect(reverse('projects_edit_participants',
        kwargs=dict(slug=participation.project.slug)))

@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.STUDY_GROUP, Project.COURSE)
def edit_participants_delete(request, slug, username):
    participation = get_object_or_404(Participation,
            project__slug=slug, user__username=username, left_on__isnull=True)
    if request.method == 'POST':
        participation.left_on = datetime.datetime.now()
        participation.save()
        msg = _("The participant %s has been removed.")
        messages.success(request, msg % participation.user)
    return http.HttpResponseRedirect(reverse(
        'projects_edit_participants',
        kwargs={'slug': participation.project.slug}))


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.CHALLENGE)
def edit_next_steps(request, slug):
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    if request.method == 'POST':
        form = project_forms.ProjectAddNextProjectForm(project, request.POST)
        if form.is_valid():
            next_project = form.cleaned_data['next_project']
            project.next_projects.add(next_project)
            messages.success(request, _('Next step added.'))
            return http.HttpResponseRedirect(reverse(
                'projects_edit_next_steps',
                kwargs=dict(slug=project.slug)))
        else:
            messages.error(request,
                _('There was an error adding that next step.'))
    else:
        form = project_forms.ProjectAddNextProjectForm(project)
    return render_to_response('projects/project_edit_next_steps.html', {
        'project': project,
        'form': form,
        'next_steps': project.next_projects.all(),
        'next_steps_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': (project.category == project.CHALLENGE),
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.CHALLENGE)
def matching_non_next_steps(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if len(request.GET['term']) == 0:
        raise http.Http404

    non_next_steps = Project.objects.exclude(
        slug=slug).exclude(
        id__in=project.next_projects.values('id'))
    matching_steps = non_next_steps.filter(deleted=False,
        slug__icontains=request.GET['term'])
    json = simplejson.dumps([step.slug for step in matching_steps])

    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
@login_required
@organizer_required
@restrict_project_kind(Project.CHALLENGE)
def edit_next_steps_delete(request, slug, step_slug):
    project = get_object_or_404(Project, slug=slug)
    next_project = get_object_or_404(project.next_projects,
        slug=step_slug)
    if request.method == 'POST':
        project.next_projects.remove(next_project)
        kwargs = {
            'name': next_project.name,
            'kind': next_project.kind.lower(),
        }
        msg = _("The %(name)s %(kind)s is not a next step anymore.")
        messages.success(request, msg % kwargs)
    return http.HttpResponseRedirect(reverse(
        'projects_edit_next_steps',
        kwargs={'slug': project.slug}))


@hide_deleted_projects
@login_required
@organizer_required
def edit_status(request, slug):
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    if request.method == 'POST':
        form = project_forms.ProjectStatusForm(
            request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            project.set_duration(form.cleaned_data['duration'])
            project.save()
            messages.success(request,
                _('%s updated!') % project.kind.capitalize())
            return http.HttpResponseRedirect(reverse('projects_edit_status', kwargs={
                'slug': project.slug,
            }))
        else:
            msg = _('There was a problem saving the %s\'s status.')
            messages.error(request, msg % project.kind.lower())
    else:
        form = project_forms.ProjectStatusForm(instance=project,
            initial={'duration': project.get_duration()})
    return render_to_response('projects/project_edit_status.html', {
        'form': form,
        'project': project,
        'status_tab': True,
        'can_view_metric_overview': metric_permissions,
        'is_challenge': (project.category == project.CHALLENGE),
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@can_view_metric_overview
def admin_metrics(request, slug):
    """Overview metrics for course organizers.

    We only are interested in the pages of the course and the participants.
    """
    project = get_object_or_404(Project, slug=slug)
    metric_permissions = project.get_metrics_permissions(request.user)
    metric_csv_permissions = project.get_metric_csv_permission(request.user)

    return render_to_response('projects/project_admin_metrics.html', {
            'project': project,
            'can_view_metric_overview': metric_permissions,
            'can_view_metric_detail': metric_csv_permissions,
            'metrics_tab': True,
            'is_challenge': (project.category == project.CHALLENGE),
    }, context_instance=RequestContext(request))


@login_required
@can_view_metric_overview
def admin_metrics_data_ajax(request, slug):
    """ returns data for jquery data tables plugin """
    project = get_object_or_404(Project, slug=slug)
    participants = project.participants(
        include_deleted=True).order_by('user__username')
    participant_profiles = (participant.user for participant in participants)
    metrics = tracker_models.metrics_summary(project, participant_profiles)
    json = simplejson.dumps(
        {'aaData': list(metrics)},
        default=json_date_encoder)
    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
@login_required
@can_view_metric_detail
def export_detailed_csv(request, slug):
    """Display detailed CSV for certain users."""
    project = get_object_or_404(Project, slug=slug)
    # Preprocessing
    organizers = project.organizers(include_deleted=True).order_by('user__username')
    organizer_profiles = (organizer.user for organizer in organizers)
    organizer_ids = organizers.values('user_id')
    participants = project.non_organizer_participants(include_deleted=True).order_by(
        'user__username')
    participant_profiles = (participant.user for participant in participants)
    participant_ids = participants.values('user_id')
    followers = project.non_participant_followers(include_deleted=True).order_by(
        'source__username')
    follower_profiles = (follower.source for follower in followers)
    follower_ids = followers.values('source_id')
    previous_followers = project.previous_followers(include_deleted=True).order_by(
        'source__username')
    previous_follower_profiles = (previous.source for previous
        in previous_followers)
    previous_follower_ids = project.previous_followers().values('source_id')
    headers = ["Time on Pages", "Non-zero Length Page Views",
        "Zero-length Page Views", "Comments", "Page Edits"]
    # Create csv response
    response = http.HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; '
    response['Content-Disposition'] += 'filename=detailed_report.csv'
    writer = unicodecsv.writer(response)
    writer.writerow(["Course: " + project.name])
    writer.writerow(["Data generated: " + datetime.datetime.now().strftime(
        "%b %d, %Y")])
    writer.writerow([])
    writer.writerow([])
    # Write Total Metrics
    writer.writerow(["TOTALS"])
    writer.writerow(["Organizers"] + headers)
    metrics = tracker_models.user_total_metrics(project,
        organizer_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Participants"] + headers)
    metrics = tracker_models.user_total_metrics(project,
        participant_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Followers"] + headers)
    for row in tracker_models.user_total_metrics(project, follower_profiles):
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Previous Followers"] + headers)
    metrics = tracker_models.user_total_metrics(project,
        previous_follower_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Unauthenticated Visitors"] + headers)
    for row in tracker_models.unauth_total_metrics(project):
        writer.writerow(row + ["0"] * 2)
    writer.writerow([])
    writer.writerow([])
    # Restoring profile iterators
    organizer_profiles = (organizer.user for organizer in organizers)
    participant_profiles = (participant.user for participant in participants)
    follower_profiles = (follower.source for follower in followers)
    previous_follower_profiles = (previous.source for previous
        in previous_followers)
    # Write Per Page Total Metrics
    writer.writerow(["PER PAGE TOTALS"])
    writer.writerow(["Organizers", "Page Paths"] + headers[:-2])
    metrics = tracker_models.user_total_per_page_metrics(project,
        organizer_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Participants", "Page Paths"] + headers[:-2])
    metrics = tracker_models.user_total_per_page_metrics(project,
        participant_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Followers", "Page Paths"] + headers[:-2])
    metrics = tracker_models.user_total_per_page_metrics(project, follower_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Previous Followers", "Page Paths"] + headers[:-2])
    metrics = tracker_models.user_total_per_page_metrics(project,
        previous_follower_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Unauthenticated Visitors", "Page Paths"] + headers[:-2])
    for row in tracker_models.unauth_total_per_page_metrics(project):
        writer.writerow(row)
    writer.writerow([])
    writer.writerow([])
    # Write Chronological Metrics
    writer.writerow(["CHRONOLOGICAL"])
    writer.writerow(["Organizers", "Dates"] + headers)
    metrics = tracker_models.chronological_user_metrics(project,
        organizer_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Participants", "Dates"] + headers)
    metrics = tracker_models.chronological_user_metrics(project,
        participant_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Followers", "Dates"] + headers)
    metrics = tracker_models.chronological_user_metrics(project,
        follower_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Previous Followers", "Dates"] + headers)
    metrics = tracker_models.chronological_user_metrics(project,
        previous_follower_profiles)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Unauthenticated Visitors", "Dates"] + headers)
    for row in tracker_models.chronological_unauth_metrics(project):
        writer.writerow(row + ["0"] * 2)
    writer.writerow([])
    writer.writerow([])
    # Write Chronological Per Page Metrics
    writer.writerow(["CHRONOLOGICAL PER PAGE"])
    writer.writerow(["Organizers", "Dates", "Page Paths"] + headers[:-2])
    metrics = tracker_models.chronological_user_per_page_metrics(
        project, organizer_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Participants", "Dates", "Page Paths"] + headers[:-2])
    metrics = tracker_models.chronological_user_per_page_metrics(
        project, participant_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Followers", "Dates", "Page Paths"] + headers[:-2])
    metrics = tracker_models.chronological_user_per_page_metrics(
        project, follower_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Previous Followers", "Dates",
        "Page Paths"] + headers[:-2])
    metrics = tracker_models.chronological_user_per_page_metrics(project,
        previous_follower_ids)
    for row in metrics:
        writer.writerow(row)
    writer.writerow([])
    writer.writerow(["Unauthenticated Visitors", "Dates",
        "Page Paths"] + headers[:-2])
    for row in tracker_models.chronological_unauth_per_page_metrics(project):
        writer.writerow(row)
    writer.writerow([])
    writer.writerow([])

    return response


@hide_deleted_projects
@login_required
@restrict_project_kind(Project.STUDY_GROUP, Project.COURSE)
def contact_organizers(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.method == 'POST':
        form = project_forms.ProjectContactOrganizersForm(request.POST)
        if form.is_valid():
            form.save(sender=request.user)
            messages.info(request,
                          _("Message successfully sent."))
            return http.HttpResponseRedirect(project.get_absolute_url())
    else:
        form = project_forms.ProjectContactOrganizersForm()
        form.fields['project'].initial = project.pk
    return render_to_response('projects/contact_organizers.html', {
        'form': form,
        'project': project,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
def task_list(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.category == Project.CHALLENGE:
        return http.HttpResponseRedirect(project.get_absolute_url())
    tasks = Page.objects.filter(project__pk=project.pk, listed=True,
        deleted=False).order_by('index')
    context = {
        'project': project,
        'tasks': tasks,
    }
    return render_to_response('projects/project_task_list.html', context,
        context_instance=RequestContext(request))


@hide_deleted_projects
def discussion_area(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.category != Project.CHALLENGE:
        return http.HttpResponseRedirect(project.get_absolute_url())
    else:
        return show(request, slug=slug, toggled_tasks=False)


@hide_deleted_projects
def user_list(request, slug):
    """Display full list of users for the project."""
    project = get_object_or_404(Project, slug=slug)
    projects_users_url = reverse('projects_user_list',
        kwargs=dict(slug=project.slug))
    context = {
        'project': project,
        'projects_users_url': projects_users_url,
        'is_challenge': (project.category == Project.CHALLENGE),
    }
    return render_to_response('projects/project_user_list.html', context,
        context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@participation_required
@restrict_project_kind(Project.CHALLENGE)
def toggle_task_completion(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug,
        listed=True, deleted=False)
    profile = request.user.get_profile()
    if request.method == 'POST':
        try:
            task_completion = PerUserTaskCompletion.objects.get(
                user=profile, page=page, unchecked_on__isnull=True)
            task_completion.unchecked_on = datetime.datetime.today()
            task_completion.save()
        except PerUserTaskCompletion.DoesNotExist:
            task_completion = PerUserTaskCompletion(user=profile, page=page)
            task_completion.save()
        context = task_toggle_completion(request, page, ignore_post_data=True)
        data = context['ajax_data']
        data['toggle_task_completion_form_html'] = render_to_string(
            'content/_toggle_completion.html',
            context, context_instance=RequestContext(request)).strip()
        json = simplejson.dumps(data)
        return http.HttpResponse(json, mimetype="application/json")

    raise http.Http404
