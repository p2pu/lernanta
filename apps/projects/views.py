import logging
import datetime

from django import http
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.utils import simplejson
from django.template.loader import render_to_string

from commonware.decorators import xframe_sameorigin

from links import tasks

from projects import forms as project_forms
from projects.decorators import organizer_required
from projects.models import Project, Participation
from projects import drupal

from l10n.urlresolvers import reverse
from relationships.models import Relationship
from links.models import Link
from users.models import UserProfile
from content.models import Page
from schools.models import School
from statuses import forms as statuses_forms 
from activity.models import Activity

from drumbeat import messages
from users.decorators import login_required
from challenges.models import Challenge

log = logging.getLogger(__name__)


def project_list(request):
    return render_to_response('projects/gallery.html', {},
                              context_instance=RequestContext(request))

def list_all(request, page=1):
    school = None
    if 'school' in request.GET:
        try:
            school = School.objects.get(slug=request.GET['school'])
            form = project_forms.CreateProjectForm(initial={'school': school})
        except School.DoesNotExist:
            return http.HttpResponseRedirect(reverse('projects_directory'))
    projects = Project.objects.filter(not_listed=False).order_by('name')
    if school:
        projects = projects.filter(school=school).exclude(id__in=school.declined.values('id'))
    paginator = Paginator(projects, 24)
    try:
        current_page = paginator.page(page)
    except EmptyPage:
        raise http.Http404
    projects = current_page.object_list
    for project in projects:
        project.followers_count = Relationship.objects.filter(
            target_project=project).count()
    return render_to_response('projects/directory.html', {
        'paginator': paginator,
        'page_num': page,
        'next_page': int(page) + 1,
        'prev_page': int(page) - 1,
        'num_pages': paginator.num_pages,
        'page': current_page,
        'school': school,
    }, context_instance=RequestContext(request))


@login_required
def create(request):
    user = request.user.get_profile()
    school = None
    if request.method == 'POST':
        form = project_forms.CreateProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            act = Activity(actor=user,
                verb='http://activitystrea.ms/schema/1.0/post',
                project=project,
                target_project=project)
            act.save()
            participation = Participation(project= project, user=user, organizing=True)
            participation.save()
            new_rel = Relationship(source=user, target_project=project)
            try:
                new_rel.save()
            except IntegrityError:
                pass
            detailed_description_content = render_to_string(
                "projects/detailed_description_initial_content.html",
                {})
            detailed_description = Page(title=_('Full Description'), slug='full-description',
                content=detailed_description_content, listed=False,
                author_id=user.id, project_id=project.id)
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            sign_up_content = render_to_string("projects/sign_up_initial_content.html",
                {})
            sign_up = Page(title=_('Sign-Up'), slug='sign-up',
                content=sign_up_content, listed=False, editable=False,
                author_id=user.id, project_id=project.id)
            sign_up.save()
            project.sign_up_id = sign_up.id
            project.create()
            messages.success(request, _('The %s has been created.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                _("There was a problem creating the %s.") % project.kind.lower())
    else:
        if 'school' in request.GET:
            try:
                school = School.objects.get(slug=request.GET['school'])
                form = project_forms.CreateProjectForm(initial={'school': school})
            except School.DoesNotExist:
                return http.HttpResponseRedirect(reverse('projects_create'))
        else:
            form = project_forms.CreateProjectForm()
    return render_to_response('projects/project_edit_summary.html', {
        'form': form, 'new_tab': True, 'school': school,
    }, context_instance=RequestContext(request))


def matching_kinds(request):
    if len(request.GET['term']) == 0:
        matching_kinds = Project.objects.values_list('kind').distinct()
    else:
        matching_kinds = Project.objects.filter(kind__icontains=request.GET['term']).values_list('kind').distinct()
    json = simplejson.dumps([kind[0] for kind in matching_kinds])

    return HttpResponse(json, mimetype="application/x-javascript")


def show(request, slug, page=1):
    project = get_object_or_404(Project, slug=slug)
    is_organizing = project.is_organizing(request.user)
    is_participating = project.is_participating(request.user)
    is_following = project.is_following(request.user)
    content_pages = Page.objects.filter(project__pk=project.pk, listed=True, deleted=False).order_by('index')
    content_pages_for_header = content_pages[0:3]
    content_pages_count = len(content_pages)
    if request.user.is_authenticated():
        is_pending_signup = project.is_pending_signup(request.user.get_profile())
    else:
        is_pending_signup = False
    if is_organizing:
        form = statuses_forms.ImportantStatusForm()
    elif is_participating:
         form = statuses_forms.StatusForm()
    else:
        form = None
    # TODO: See how we can modify and use challenges.
    challenges = Challenge.objects.upcoming(project_id=project.id)

    activities = project.activities()
    paginator = Paginator(activities, 10)
    try:
        current_page = paginator.page(page)
    except EmptyPage:
        raise http.Http404
    
    context = {
        'project': project,
        'participating': is_participating,
        'following': is_following,
        'pending_signup': is_pending_signup,
        'organizing': is_organizing,
        'challenges': challenges,
        'content_pages_for_header': content_pages_for_header,
        'content_pages_count': content_pages_count,
        'form': form,
        'paginator': paginator,
        'page_num': page,
        'next_page': int(page) + 1,
        'prev_page': int(page) - 1,
        'num_pages': paginator.num_pages,
        'page': current_page,
    }
    return render_to_response('projects/project.html', context,
                              context_instance=RequestContext(request))

@login_required
def clone(request):
    user = request.user.get_profile()
    if 'school' in request.GET:
        try:
            school = School.objects.get(slug=request.GET['school'])
        except School.DoesNotExist:
            return http.HttpResponseRedirect(reverse('projects_clone'))
    else:
        school = None
    if request.method == 'POST':
        form = project_forms.CloneProjectForm(school, request.POST)
        if form.is_valid():
            base_project = form.cleaned_data['project']
            project = Project(name=base_project.name, kind=base_project.kind,
                short_description=base_project.short_description,
                long_description=base_project.long_description,
                school=base_project.school, clone_of=base_project)
            project.save()
            act = Activity(actor=user,
                verb='http://activitystrea.ms/schema/1.0/post',
                project=project,
                target_project=project)
            act.save()
            participation = Participation(project=project, user=user, organizing=True)
            participation.save()
            new_rel = Relationship(source=user, target_project=project)
            try:
                new_rel.save()
            except IntegrityError:
                pass
            detailed_description = Page(title=_('Full Description'), slug='full-description',
                content=base_project.detailed_description.content, listed=False,
                author_id=user.id, project_id=project.id)
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            sign_up = Page(title=_('Sign-Up'), slug='sign-up',
                content=base_project.sign_up.content, listed=False, editable=False,
                author_id=user.id, project_id=project.id)
            sign_up.save()
            project.sign_up_id = sign_up.id
            project.save()
            tasks = Page.objects.filter(project=base_project, listed=True,
                deleted=False).order_by('index')
            for task in tasks:
                new_task = Page(title=task.title, content=task.content, author=user,
                    project=project)
                new_task.save()
            links = Link.objects.filter(project=base_project).order_by('index')
            for link in links:
                new_link = Link(name=link.name, url=link.url, user=user, project=project)
                new_link.save()
            messages.success(request, _('The %s has been cloned.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                _("There was a problem cloning the %s.") % project.kind.lower())
    else:
        form = project_forms.CloneProjectForm(school)
    return render_to_response('projects/project_clone.html', {
        'form': form, 'clone_tab': True, 'school': school,
    }, context_instance=RequestContext(request))


def matching_projects(request):
    if len(request.GET['term']) == 0:
        raise CommandException(_("Invalid request"))

    if 'school' in request.GET:
        try:
            school = School.objects.get(slug=request.GET['school'])
            projects = Project.objects.filter(school=school)
        except School.DoesNotExist:
            projects = Project.objects.all()
    else:
        projects = Project.objects.all()
    matching_projects = projects.filter(slug__icontains = request.GET['term'])
    json = simplejson.dumps([project.slug for project in matching_projects])

    return HttpResponse(json, mimetype="application/x-javascript")


@login_required
def import_from_old_site(request):
    user = request.user.get_profile()
    if 'school' in request.GET:
        try:
            school = School.objects.get(slug=request.GET['school'])
        except School.DoesNotExist:
            return http.HttpResponseRedirect(reverse('projects_clone'))
    else:
        school = None
    if request.method == 'POST':
        form = project_forms.ImportProjectForm(school, request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            project = Project(name=course['name'], kind=course['kind'],
                short_description= course['short_description'],
                long_description=course['long_description'],
                school=course['school'], imported_from=course['slug'])
            project.save()
            act = Activity(actor=user,
                verb='http://activitystrea.ms/schema/1.0/post',
                project=project,
                target_project=project)
            act.save()
            participation = Participation(project=project, user=user, organizing=True)
            participation.save()
            new_rel = Relationship(source=user, target_project=project)
            try:
                new_rel.save()
            except IntegrityError:
                pass
            if course['detailed_description']:
                detailed_description_content = course['detailed_description']
            else:
                detailed_description_content = render_to_string(
                    "projects/detailed_description_initial_content.html",
                    {})
            detailed_description = Page(title=_('Full Description'), slug='full-description',
                content=detailed_description_content, listed=False,
                author_id=user.id, project_id=project.id)
            detailed_description.save()
            project.detailed_description_id = detailed_description.id
            sign_up_content = render_to_string("projects/sign_up_initial_content.html",
                {})
            sign_up = Page(title=_('Sign-Up'), slug='sign-up',
                content=sign_up_content, listed=False, editable=False,
                author_id=user.id, project_id=project.id)
            sign_up.save()
            project.sign_up_id = sign_up.id
            project.save()
            for title, content in course['tasks']:
                new_task = Page(title=title, content=content, author=user,
                    project=project)
                new_task.save()
            for name, url in course['links']:
                new_link = Link(name=name, url=url, user=user, project=project)
                new_link.save()
            messages.success(request, _('The %s has been imported.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                _("There was a problem importing the %s.") % project.kind.lower())
    else:
        form = project_forms.ImportProjectForm(school)
    return render_to_response('projects/project_import.html', {
        'form': form, 'import_tab': True, 'school': school,
    }, context_instance=RequestContext(request))


def matching_courses(request):
    if len(request.GET['term']) == 0:
        raise CommandException(_("Invalid request"))
    school = None
    if 'school' in request.GET:
        try:
            school = School.objects.get(slug=request.GET['school'])
        except School.DoesNotExist:
            pass
    matching_nodes = drupal.get_matching_courses(school=school, term=request.GET['term'])
    json = simplejson.dumps(matching_nodes)

    return HttpResponse(json, mimetype="application/x-javascript")


@login_required
@organizer_required
def edit(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.method == 'POST':
        form = project_forms.ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, _('%s updated!') % project.kind.capitalize())
            return http.HttpResponseRedirect(
                reverse('projects_edit', kwargs=dict(slug=project.slug)))
    else:
        school = project.school
        if school and school.declined.filter(id=project.id).exists():
            msg = _('The %(kind)s membership to %(school)s was declined by the school organizers.') % dict(kind = project.kind.lower(), school = school.name)
            messages.error(request, msg)
        form = project_forms.ProjectForm(instance=project)

    return render_to_response('projects/project_edit_summary.html', {
        'form': form,
        'project': project,
        'summary_tab': True,
    }, context_instance=RequestContext(request))


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


@login_required
@organizer_required
def edit_image(request, slug):
    project = get_object_or_404(Project, slug=slug)
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
    }, context_instance=RequestContext(request))


@login_required 
@organizer_required
def edit_links(request, slug):
    project = get_object_or_404(Project, slug=slug)
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
    }, context_instance=RequestContext(request))


@login_required   
@organizer_required
def edit_links_edit(request, slug, link):
    link = get_object_or_404(Link, id=link)
    form = project_forms.ProjectLinksForm(request.POST or None, instance=link)
    profile = get_object_or_404(UserProfile, user=request.user)
    project = get_object_or_404(Project, slug=slug)
    if link.project != project:
        return http.HttpResponseForbidden(_("You can't edit this link"))
    if form.is_valid():
        if link.subscription:
            tasks.UnsubscribeFromFeed.apply_async(args=(link,))
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
    }, context_instance=RequestContext(request))

    
@login_required
@organizer_required
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


@login_required
@organizer_required
def edit_participants(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.method == 'POST':
        form = project_forms.ProjectAddParticipantForm(project, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            organizing = form.cleaned_data['organizer']
            participation = Participation(project=project, user=user, organizing=organizing)
            participation.save()
            new_rel = Relationship(source=user, target_project=project)
            try:
                new_rel.save()
            except IntegrityError:
                pass
            messages.success(request, _('Participant added.'))
            return http.HttpResponseRedirect(
                reverse('projects_edit_participants', kwargs=dict(slug=project.slug)))
        else:
            messages.error(request, _('There was an error adding the participant.'))
    else:
        form = project_forms.ProjectAddParticipantForm(project)
    return render_to_response('projects/project_edit_participants.html', {
        'project': project,
        'form': form,
        'participations': project.participants().order_by('joined_on'),
        'participants_tab': True,
    }, context_instance=RequestContext(request))


def matching_non_participants(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if len(request.GET['term']) == 0:
        raise CommandException(_("Invalid request"))

    non_participants = UserProfile.objects.exclude(deleted=False, id__in=project.participants().values('user_id'))
    matching_users = non_participants.filter(username__icontains = request.GET['term'])
    json = simplejson.dumps([user.username for user in matching_users])

    return HttpResponse(json, mimetype="application/x-javascript")


@login_required
@organizer_required
def edit_participants_make_organizer(request, slug, username):
    participation = get_object_or_404(Participation,
            project__slug=slug, user__username=username, left_on__isnull=True)
    if participation.organizing or request.method != 'POST':
        return HttpResponseForbidden(_("You can't make that person an organizer"))
    participation.organizing = True
    participation.save()
    messages.success(request, _('The participant is now an organizer.'))
    return http.HttpResponseRedirect(reverse('projects_edit_participants',
        kwargs=dict(slug=participation.project.slug)))


@login_required
@organizer_required
def edit_participants_delete(request, slug, username):
    participation = get_object_or_404(Participation,
            project__slug=slug, user__username=username, left_on__isnull=True)
    if request.method == 'POST':
        participation.left_on = datetime.datetime.now()
        participation.save()
        messages.success(request, _(
            "The participant %s has been removed." % participation.user.display_name))
    return http.HttpResponseRedirect(reverse('projects_edit_participants', kwargs={
        'slug': participation.project.slug,
    }))


@login_required
@organizer_required
def edit_status(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.method == 'POST':
        form = project_forms.ProjectStatusForm(
            request.POST, instance=project)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(reverse('projects_show', kwargs={
                'slug': project.slug,
            }))
        else:
            messages.error(request,
                           _('There was a problem saving the %s\'s status.') % project.kind.lower())
    else:
        form = project_forms.ProjectStatusForm(instance=project)
    return render_to_response('projects/project_edit_status.html', {
        'form': form,
        'project': project,
        'status_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def contact_organizers(request, slug):
    project = get_object_or_404(Project, slug=slug)
    user = request.user.get_profile()
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


def task_list(request, slug):
        project = get_object_or_404(Project, slug=slug)
        tasks = Page.objects.filter(project__pk=project.pk, listed=True, deleted=False).order_by('index')
        
        context = {
        'project': project,
        'tasks': tasks,
        }
        return render_to_response('projects/project_task_list.html', context,
                              context_instance=RequestContext(request))
