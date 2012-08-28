import datetime
from urlparse import urlsplit

from django.shortcuts import render_to_response, get_object_or_404
from django import http
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.utils import simplejson
from django.forms.models import modelformset_factory

from l10n.urlresolvers import reverse
from users.decorators import login_required
from drumbeat import messages
from projects.decorators import participation_required, hide_deleted_projects
from projects.models import Project
from pagination.views import get_pagination_context
from projects.decorators import restrict_project_kind
from tracker.models import get_google_tracking_context

from content.forms import PageForm, NotListedPageForm
from content.forms import OwnersPageForm, OwnersNotListedPageForm
from content.models import Page, PageVersion
from content.templatetags.content_tags import task_toggle_completion

import logging
log = logging.getLogger(__name__)

@hide_deleted_projects
def show_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    is_challenge = (page.project.category == Project.CHALLENGE)
    if is_challenge and not page.listed:
        msg = _("This page is not accesible on a %s.")
        return http.HttpResponseForbidden(msg % page.project.kind.lower())
    can_edit = page.can_edit(request.user)
    if page.deleted:
        messages.error(request, _('This task was deleted.'))
        if can_edit:
            return http.HttpResponseRedirect(reverse('page_history',
                kwargs={'slug': page.project.slug, 'page_slug': page.slug}))
        else:
            return http.HttpResponseRedirect(page.project.get_absolute_url())
    new_comment_url = reverse('page_comment', kwargs=dict(
        scope_app_label='projects', scope_model='project',
        scope_pk=page.project.id, page_app_label='content',
        page_model='page', page_pk=page.id))
    first_level_comments = page.first_level_comments()
    all_listed_pages = page.project.pages.filter(deleted=False,
        listed=True).order_by('index')

    context = {
        'page': page,
        'project': page.project,
        'can_edit': can_edit,
        'can_comment': page.can_comment(request.user),
        'new_comment_url': new_comment_url,
        'is_challenge': is_challenge,
        'all_listed_pages': all_listed_pages,
    }
    context.update(get_pagination_context(request, first_level_comments))
    context.update(get_google_tracking_context(page.project))

    return render_to_response('content/page.html', context,
            context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@participation_required
@restrict_project_kind(Project.CHALLENGE)
def link_submit(request, slug, page_slug):
    page = get_object_or_404(Page, slug=page_slug, project__slug=slug,
        listed=True, deleted=False)
    context = task_toggle_completion(request, page)
    data = context['ajax_data']
    data['toggle_task_completion_form_html'] = render_to_string(
        'content/_toggle_completion.html',
        context, context_instance=RequestContext(request)).strip()
    json = simplejson.dumps(data)
    return http.HttpResponse(json, mimetype="application/json")


@hide_deleted_projects
@login_required
@participation_required
def edit_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if page.deleted:
        return http.HttpResponseForbidden(_("You can't edit this page"))
    if page.project.is_organizing(request.user):
        form_cls = OwnersPageForm if page.listed else OwnersNotListedPageForm
    elif page.collaborative:
        form_cls = PageForm if page.listed else NotListedPageForm
    else:
        # Restrict permissions for non-collaborative pages.
        return http.HttpResponseForbidden(_("You can't edit this page"))
    if request.method == 'POST':
        old_version = PageVersion(title=page.title, content=page.content,
            author=page.author, date=page.last_update, page=page)
        form = form_cls(request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            page.author = request.user.get_profile()
            page.last_update = datetime.datetime.now()
            if 'show_preview' not in request.POST:
                old_version.save()
                page.save()
                messages.success(request, _('%s updated!') % page.title)
                if form.cleaned_data.get('next_url', None):
                    return http.HttpResponseRedirect(
                        form.cleaned_data.get('next_url'))
                else:
                    return http.HttpResponseRedirect(reverse('page_show',
                        kwargs={ 'slug': slug, 'page_slug': page_slug }))
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        initial={'minor_update': True}
        if request.GET.get('next_url', None):
            initial['next_url'] = request.GET.get('next_url', None)
        form = form_cls(instance=page, initial=initial)
       
    context = {
        'form': form,
        'page': page,
        'project': page.project,
        'preview': ('show_preview' in request.POST),
        'is_challenge': (page.project.category == Project.CHALLENGE),
    }
    
    return render_to_response('content/edit_page.html', context,
        context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@participation_required
def create_page(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.is_organizing(request.user):
        form_cls = OwnersPageForm
    elif project.category == Project.STUDY_GROUP:
        form_cls = PageForm
    else:
        messages.error(request, _('You can not create a new task!'))
        return http.HttpResponseRedirect(project.get_absolute_url())
    initial = {}
    if project.category != Project.STUDY_GROUP:
        initial['collaborative'] = False
    page = None
    if request.method == 'POST':
        form = form_cls(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.project = project
            page.author = request.user.get_profile()
            if 'show_preview' not in request.POST:
                page.save()
                messages.success(request, _('Task created!'))
                if form.cleaned_data.get('next_url', None):
                    return http.HttpResponseRedirect(
                        form.cleaned_data.get('next_url'))
                else:
                    return http.HttpResponseRedirect(reverse('page_show',
                        kwargs={'slug': slug, 'page_slug': page.slug}))
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        if request.GET.get('next_url', None):
            initial['next_url'] = request.GET.get('next_url', None)
        form = form_cls(initial=initial)

    context = {
        'form': form,
        'project': project,
        'page': page,
        'preview': ('show_preview' in request.POST),
        'is_challenge': (project.category == Project.CHALLENGE),
    }
    template = 'content/create_page.html'
    
    return render_to_response(template, context,
        context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@participation_required
def delete_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if page.deleted or not page.listed:
        return http.HttpResponseForbidden(_("You can't delete this page"))
    if not page.project.is_organizing(request.user) and not page.collaborative:
        return http.HttpResponseForbidden(_("You can't delete this page"))
    if request.method == 'POST':
        redirect_url = request.POST.get('next_page', None)
        old_version = PageVersion(title=page.title, sub_header=page.sub_header,
            content=page.content, author=page.author, date=page.last_update,
            page=page)
        old_version.save()
        page.author = request.user.get_profile()
        page.last_update = datetime.datetime.now()
        page.deleted = True
        page.save()
        messages.success(request, _('%s deleted!') % page.title)
        if redirect_url:
            return http.HttpResponseRedirect(redirect_url)
        return http.HttpResponseRedirect(reverse('page_history',
            kwargs={'slug': page.project.slug, 'page_slug': page.slug}))
    else:
        context = {
            'page': page,
            'project': page.project,
        }
        referer = request.META.get('HTTP_REFERER', None)
        if referer:
            context['next_page'] = urlsplit(referer, 'http', False)[2]
        return render_to_response('content/confirm_delete_page.html',
            context, context_instance=RequestContext(request))


@hide_deleted_projects
def history_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    versions = PageVersion.objects.filter(page=page).order_by('-date')
    return render_to_response('content/history_page.html', {
        'page': page,
        'versions': versions,
        'project': page.project,
    }, context_instance=RequestContext(request))


@hide_deleted_projects
def version_page(request, slug, page_slug, version_id):
    version = get_object_or_404(PageVersion, page__project__slug=slug,
        page__slug=page_slug, id=version_id, deleted=False)
    page = version.page
    return render_to_response('content/version_page.html', {
        'page': page,
        'version': version,
        'project': page.project,
        'can_edit': page.can_edit(request.user),
    }, context_instance=RequestContext(request))


@hide_deleted_projects
@login_required
@participation_required
def restore_version(request, slug, page_slug, version_id):
    version = get_object_or_404(PageVersion, page__project__slug=slug,
        page__slug=page_slug, id=version_id)
    page = version.page
    if version.deleted:
        return http.HttpResponseForbidden(_("You can't restore this page"))
    if page.project.is_organizing(request.user):
        form_cls = OwnersPageForm if page.listed else OwnersNotListedPageForm
    elif page.collaborative:
        form_cls = PageForm if page.listed else NotListedPageForm
    else:
        # Restrict permissions for non-collaborative pages.
        return http.HttpResponseForbidden(_("You can't edit this page"))
    if request.method == 'POST':
        old_version = PageVersion(title=page.title, sub_header=page.sub_header,
            content=page.content, author=page.author, date=page.last_update,
            page=page, deleted=page.deleted)
        form = form_cls(request.POST, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            page.deleted = False
            page.author = request.user.get_profile()
            page.last_update = datetime.datetime.now()
            if 'show_preview' not in request.POST:
                old_version.save()
                page.save()
                messages.success(request, _('%s restored!') % page.title)
                return http.HttpResponseRedirect(reverse('page_show', kwargs={
                    'slug': slug,
                    'page_slug': page_slug,
                }))
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        page.title = version.title
        page.content = version.content
        form = form_cls(instance=page, initial={'minor_update': True})
    return render_to_response('content/restore_version.html', {
        'form': form,
        'page': page,
        'version': version,
        'project': page.project,
        'preview': ('show_preview' in request.POST),
        'is_challenge': (page.project.category == Project.CHALLENGE),
    }, context_instance=RequestContext(request))

def _move_page(request, slug, page_slug, direction='up'):
    # Page goes up in the sidebar index (page.index decreases)."""
    project = get_object_or_404(Project, slug=slug)
    organizing = project.is_organizing(request.user)

    # determine redirect url to use
    redirect_to = project.get_absolute_url()
    referer = request.META.get('HTTP_REFERER', None)
    if referer:
        try:
            redirect_to = urlsplit(referer, 'http', False)[2]
        except IndexError:
            pass
    
    if not organizing and project.category != Project.STUDY_GROUP:
        messages.error(request, _('You can not change tasks order.'))
        return http.HttpResponseRedirect(redirect_to)
        
    content_pages = Page.objects.filter(project__pk=project.pk,
        listed=True, deleted=False).order_by('index')

    #find page we want to move
    index = [i for i,x in enumerate(content_pages) if x.slug == page_slug]
    if len(index) != 1 or direction=='up' and index[0] == 0 or direction=='down' and index[0] == len(content_pages)-1:
        return http.HttpResponseRedirect(redirect_to)

    if direction=='up':
        prev_page = content_pages[index[0] - 1]
        page = content_pages[index[0]]
    else:
        prev_page = content_pages[index[0] + 1]
        page = content_pages[index[0]]
    prev_page.index, page.index = page.index, prev_page.index
    # TODO: Fix this so no update messages are added to the wall but
    # we don't loose the data for the minor_update field of PageVersion.
    # For now relly on the Activity model to store this information.
    page.minor_update = prev_page.minor_update = True
    page.save()
    prev_page.save()
    
    if referer:
        return http.HttpResponseRedirect(redirect_to)

    return http.HttpResponseRedirect(project.get_absolute_url() + '#tasks')

@hide_deleted_projects
@login_required
@participation_required
def page_index_up(request, slug, page_slug):
    # Page goes up in the sidebar index (page.index decreases)."""
    return _move_page(request, slug, page_slug, 'up')


@hide_deleted_projects
@login_required
@participation_required
def page_index_down(request, slug, page_slug):
    # Page goes down in the sidebar index (page.index increases).
    return _move_page(request, slug, page_slug, 'down')


@hide_deleted_projects
@login_required
@participation_required
def page_index_reorder(request, slug):
    project = get_object_or_404(Project, slug=slug)
    organizing = project.is_organizing(request.user)
    if not organizing and project.category != Project.STUDY_GROUP:
        messages.error(request, _('You can not change tasks order.'))
        return http.HttpResponseRedirect(project.get_absolute_url())

    # newIndex = int(request.POST['newIndex']) + 1  # task indices are 1-based
    content_pages = Page.objects.filter(project__pk=project.pk, listed=True,
        deleted=False,
    )
    if content_pages.count() <= 0:
        raise http.Http404

    task_new_order = request.POST.getlist('tasks[]')
    for i in range(len(task_new_order)):
        task = content_pages.filter(slug=task_new_order[i])
        if (len(task) > 1):
            raise http.Http404
        task[0].index = i + 1
        task[0].save()
    #refresh tasks
    content_pages = Page.objects.filter(project__pk=project.pk, listed=True,
        deleted=False,
    ).order_by('index')

    #tasks = content_pages.values()
    tasks = []
    for task in (content_pages):
        tasks.append({"title": task.title,
                     "href": task.get_absolute_url(),
                     "bttnUpUrl": reverse('page_index_up',
                         kwargs={'slug': project.slug, 
                                'page_slug': task.slug}),
                     "bttnDownUrl": reverse('page_index_down',
                         kwargs={'slug': project.slug,
                                'page_slug': task.slug}),
    })

    json = simplejson.dumps(tasks)
    return http.HttpResponse(json, mimetype="application/json")
