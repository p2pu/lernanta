import datetime

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import IntegrityError

from l10n.urlresolvers import reverse
from users.decorators import login_required
from users.forms import ProfileEditForm, ProfileImageForm
from drumbeat import messages
from projects.decorators import participation_required, organizer_required
from projects.models import Project, Participation
from relationships.models import Relationship

from content.forms import PageForm, NotListedPageForm, CommentForm, OwnersPageForm, OwnersNotListedPageForm
from content.models import Page, PageVersion, PageComment
from links.models import Link


def show_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    can_edit = page.can_edit(request.user)
    if page.deleted:
        messages.error(request, _('This task was deleted.'))
        if can_edit:
            return HttpResponseRedirect(reverse('page_history', kwargs={'slug':page.project, 'page_slug':page.slug}))
        else:
            return HttpResponseRedirect(page.project.get_absolute_url())
    first_level_comments = page.comments.filter(reply_to__isnull=True)
    return render_to_response('content/page.html', {
        'page': page,
        'project': page.project,
        'can_edit': can_edit,
        'first_level_comments': first_level_comments,
    }, context_instance=RequestContext(request))

def show_comment(request, slug, page_slug, comment_id):
    comment = get_object_or_404(PageComment, page__project__slug=slug, page__slug=page_slug,
        id=comment_id)
    page_url = comment.page.get_absolute_url()
    if comment.deleted:
        if page_slug == 'sign-up' and not comment.reply_to:
            msg = _('This answer was deleted.')
        else:
            msg = _('This comment was deleted.')
        messages.error(request, msg)
        if comment.can_edit(request.user):
            return HttpResponseRedirect(reverse('comment_restore', kwargs={'slug': comment.page.project.slug,
                'page_slug': comment.page.slug, 'comment_id': comment.id}))
        else:
            return HttpResponseRedirect(page_url)
    else:
        return HttpResponseRedirect(page_url + '#%s' % comment.id)


@login_required
@participation_required
def edit_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if not page.editable or page.deleted:
        return HttpResponseForbidden()
    if page.project.is_organizing(request.user):
        form_cls = OwnersPageForm if page.listed else OwnersNotListedPageForm
    elif page.collaborative:
        form_cls = PageForm if page.listed else NotListedPageForm
    else:
        # Restrict permissions for non-collaborative pages.
        return HttpResponseForbidden()
    if request.method == 'POST':
        old_version = PageVersion(title=page.title, content=page.content,
            author=page.author, date=page.last_update, page=page)
        form = form_cls(request.POST, instance=page)
        if form.is_valid():
            old_version.save()
            page = form.save(commit=False)
            page.author = request.user.get_profile()
            page.last_update = datetime.datetime.now()
            page.save()
            messages.success(request, _('%s updated!') % page.title)
            return HttpResponseRedirect(reverse('page_show', kwargs={
                'slug': slug,
                'page_slug': page_slug,
            }))
        else:
            messages.error(request,
                           _('There was a problem saving %s.' % page.title))
    else:
        form = form_cls(instance=page)
    return render_to_response('content/edit_page.html', {
        'form': form,
        'page': page,
        'project': page.project,
    }, context_instance=RequestContext(request))

@login_required
@participation_required
def create_page(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.is_organizing(request.user):
        form_cls = OwnersPageForm
    else:
        form_cls = PageForm
    if request.method == 'POST':
        form = form_cls(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.project = project
            page.author = request.user.get_profile()
            page.save()
            messages.success(request, _('Task created!'))
            return HttpResponseRedirect(reverse('page_show', kwargs={
                'slug': slug,
                'page_slug': page.slug,
            }))
        else:
            messages.error(request,
                           _('There was a problem creating the task.'))
    else:
        form = form_cls()
    return render_to_response('content/create_page.html', {
        'form': form,
        'project': project,
    }, context_instance=RequestContext(request))


@login_required
@participation_required
def delete_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if page.deleted or not page.editable or not page.listed:
        return HttpResponseForbidden()
    if not page.project.is_organizing(request.user) and not page.collaborative:
        return HttpResponseForbidden()
    if request.method == 'POST':
        old_version = PageVersion(title=page.title, content=page.content,
            author=page.author, date=page.last_update, page=page)
        old_version.save()
        page.author = request.user.get_profile()
        page.last_update = datetime.datetime.now()
        page.deleted = True
        page.save()
        messages.success(request, _('%s deleted!') % page.title)
        return HttpResponseRedirect(reverse('page_history',
            kwargs={'slug':page.project, 'page_slug':page.slug}))
    else:
        return render_to_response('content/confirm_delete_page.html', {
            'page': page,
            'project': page.project,
        }, context_instance=RequestContext(request))



@login_required
@participation_required
def comment_page(request, slug, page_slug, comment_id=None):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if not page.editable:
        return HttpResponseForbidden()
    user = request.user.get_profile()
    reply_to = abs_reply_to = None
    if comment_id:
        reply_to = page.comments.get(pk=comment_id)
        abs_reply_to = reply_to
        while abs_reply_to.reply_to:
            abs_reply_to = abs_reply_to.reply_to
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.page = page
            comment.author = user
            comment.reply_to = reply_to
            comment.abs_reply_to = abs_reply_to
            comment.save()
            messages.success(request, _('Comment posted!'))
            return HttpResponseRedirect(reverse('page_show', kwargs={
                'slug': slug,
                'page_slug': page.slug,
            }))
        else:
            messages.error(request,
                           _('There was a problem posting the comment. Comments cannot be empty.'))
    else:
        form = CommentForm()
    return render_to_response('content/comment_page.html', {
        'form': form,
        'project': page.project,
        'page': page,
        'reply_to': reply_to,
    }, context_instance=RequestContext(request))


@login_required
@participation_required
def edit_comment(request, slug, page_slug, comment_id):
    comment = get_object_or_404(PageComment, id=comment_id, page__slug=page_slug, page__project__slug=slug)
    if not comment.can_edit(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, _('Comment updated!'))
            return HttpResponseRedirect(comment.get_absolute_url())
        else:
            messages.error(request,
                           _('There was a problem saving the comment.'))
    else:
        form = CommentForm(instance=comment)
    return render_to_response('content/comment_page.html', {
        'form': form,
        'comment': comment,
        'page': comment.page,
        'project': comment.page.project,
    }, context_instance=RequestContext(request))


@login_required
def delete_restore_comment(request, slug, page_slug, comment_id):
    comment = get_object_or_404(PageComment, id=comment_id, page__slug=page_slug, page__project__slug=slug)
    if not comment.can_edit(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        comment.deleted = not comment.deleted
        comment.save()
        if comment.page.slug == 'sign-up' and not comment.reply_to:
            msg = _('Answer deleted!') if comment.deleted else _('Answer restored!')
        else:
            msg = _('Comment deleted!') if comment.deleted else _('Comment restored!')
        messages.success(request, msg)
        if comment.deleted:
            return HttpResponseRedirect(comment.page.get_absolute_url())
        else:
            return HttpResponseRedirect(comment.get_absolute_url())
    else:
        return render_to_response('content/delete_restore_comment.html', {
            'comment': comment,
            'page': comment.page,
            'project': comment.page.project,
        }, context_instance=RequestContext(request))


def history_page(request, slug, page_slug):
    page = get_object_or_404(Page, project__slug=slug, slug=page_slug)
    if not page.editable:
        return HttpResponseForbidden()
    versions = PageVersion.objects.filter(page=page).order_by('-date')
    return render_to_response('content/history_page.html', {
        'page': page,
        'versions': versions,
        'project': page.project,
    }, context_instance=RequestContext(request))


def version_page(request, slug, page_slug, version_id):
    version = get_object_or_404(PageVersion, page__project__slug=slug,
        page__slug=page_slug, id=version_id, deleted=False)
    page = version.page
    if not page.editable:
        return HttpResponseForbidden()
    return render_to_response('content/version_page.html', {
        'page': page,
        'version': version,
        'project': page.project,
        'can_edit': page.can_edit(request.user),
    }, context_instance=RequestContext(request))


@login_required
@participation_required
def restore_version(request, slug, page_slug, version_id):
    version = get_object_or_404(PageVersion, page__project__slug=slug,
        page__slug=page_slug, id=version_id)
    page = version.page
    if not page.editable or version.deleted:
        return HttpResponseForbidden()
    if page.project.is_organizing(request.user):
        form_cls = OwnersPageForm if page.listed else OwnersNotListedPageForm
    elif page.collaborative:
        form_cls = PageForm if page.listed else NotListedPageForm
    else:
        # Restrict permissions for non-collaborative pages.
        return HttpResponseForbidden()
    if request.method == 'POST':
        old_version = PageVersion(title=page.title, content=page.content,
            author=page.author, date=page.last_update, page=page, deleted=page.deleted)
        form = form_cls(request.POST, instance=page)
        if form.is_valid():
            old_version.save()
            page = form.save(commit=False)
            page.deleted = False
            page.author = request.user.get_profile()
            page.last_update = datetime.datetime.now()
            page.save()
            messages.success(request, _('%s restored!') % page.title)
            return HttpResponseRedirect(reverse('page_show', kwargs={
                'slug': slug,
                'page_slug': page_slug,
            }))
        else:
            messages.error(request,
                           _('There was a problem saving %s.' % page.title))
    else:
        page.title = version.title
        page.content = version.content
        form = form_cls(instance=page)
    return render_to_response('content/restore_version.html', {
        'form': form,
        'page': page,
        'version': version,
        'project': page.project,
    }, context_instance=RequestContext(request))


def sign_up(request, slug):
    page = get_object_or_404(Page, project__slug=slug, slug='sign-up')
    project = page.project
    if request.user.is_authenticated():
        is_organizing = project.is_organizing(request.user)
        is_participating = project.is_participating(request.user)
        first_level_comments = page.comments.filter(reply_to__isnull=True)
        can_post_answer = False
        if not is_organizing:
            if is_participating:
                participants = project.participants()
                first_level_comments = first_level_comments.filter(author__in=participants.values('user_id'))
            else:
                profile = request.user.get_profile()
                first_level_comments = first_level_comments.filter(author=profile)
                can_post_answer = not first_level_comments.filter(deleted=False).exists()
    else:
        first_level_comments = []
        is_organizing = is_participating = can_post_answer = False
    if project.signup_closed:
        can_post_answer = False
    if first_level_comments:
        pending_answers_count = first_level_comments.filter(deleted=False).count()
    else:
        pending_answers_count = 0
    if is_organizing:
        for comment in first_level_comments:
             comment.is_participating = project.participants().filter(user=comment.author)
    return render_to_response('content/sign_up.html', {
        'page': page,
        'project': project,
        'organizing': is_organizing,
        'participating': is_participating,
        'first_level_comments': first_level_comments,
        'can_post_answer': can_post_answer,
        'pending_answers_count': pending_answers_count,
    }, context_instance=RequestContext(request))


@login_required
def comment_sign_up(request, slug, comment_id=None):
    page = get_object_or_404(Page, project__slug=slug, slug='sign-up')
    project = page.project
    is_organizing = project.is_organizing(request.user)
    is_participating = project.is_participating(request.user)
    user = request.user.get_profile()
    reply_to = abs_reply_to = None
    if comment_id:
        reply_to = page.comments.get(pk=comment_id)
        abs_reply_to = reply_to
        while abs_reply_to.reply_to:
            abs_reply_to = abs_reply_to.reply_to
        if not is_organizing:
            if is_participating:
                if not project.is_participating(abs_reply_to.author):
                    return HttpResponseForbidden()
            elif abs_reply_to.author != user:
                return HttpResponseForbidden()
    elif project.signup_closed or is_organizing or is_participating:
        return HttpResponseForbidden()
    else:
        answers = page.comments.filter(reply_to__isnull=True, deleted=False,
            author=user)
        if answers.exists():
            return HttpResponseForbidden()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        profile_form = ProfileEditForm(request.POST, instance=user)
        profile_image_form = ProfileImageForm()
        if form.is_valid() and (reply_to or profile_form.is_valid()):
            if not reply_to:
                profile_form.save()
                new_rel = Relationship(source=user, target_project=project)
                try:
                    new_rel.save()
                except IntegrityError:
                    pass
            comment = form.save(commit=False)
            comment.page = page
            comment.author = user
            comment.reply_to = reply_to
            comment.abs_reply_to = abs_reply_to
            comment.save()
            success_msg = _('Reply posted!') if reply_to else _('Answer submitted!')
            messages.success(request, success_msg)
            return HttpResponseRedirect(reverse('page_show', kwargs={
                'slug': slug,
                'page_slug': page.slug,
            }))
        else:
            error_msg = _('There was a problem posting your reply. Reply cannot be empty. ') if reply_to \
                        else _('There was a problem submitting your answer. Answer cannot be empty. ')
            
            messages.error(request, error_msg)
    else:
        profile_form = ProfileEditForm(instance=user)
        profile_image_form = ProfileImageForm()
        form = CommentForm()
    return render_to_response('content/comment_sign_up.html', {
        'profile_image_form': profile_image_form,
        'profile_form': profile_form,
        'profile': user,
        'form': form,
        'project': project,
        'page': page,
        'reply_to': reply_to,
    }, context_instance=RequestContext(request))


@login_required
def edit_comment_sign_up(request, slug, comment_id):
    comment = get_object_or_404(PageComment, page__project__slug=slug, page__slug='sign-up', id=comment_id)
    if not comment.can_edit(request.user):
        return HttpResponseForbidden()
    abs_reply_to = comment
    while abs_reply_to.reply_to:
        abs_reply_to = abs_reply_to.reply_to
    if abs_reply_to == comment:
        abs_reply_to = reply_to = None
    else:
        reply_to = comment.reply_to

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        profile_form = ProfileEditForm(request.POST, instance=comment.author)
        profile_image_form = ProfileImageForm()
        if form.is_valid() and (reply_to or profile_form.is_valid()):
            if not reply_to:
                profile_form.save()
            form.save()
            success_msg = _('Comment updated!') if reply_to else _('Answer updated!')
            messages.success(request, success_msg)
            return HttpResponseRedirect(comment.get_absolute_url())
        else:
            error_msg = _('There was a problem updating your comment. Comments cannot be empty. ') if reply_to \
                        else _('There was a problem updating your answer. Answers cannot be empty. ')
            
            messages.error(request, error_msg)
    else:
        profile_form = ProfileEditForm(instance=comment.author)
        profile_image_form = ProfileImageForm()
        form = CommentForm(instance=comment)
    return render_to_response('content/comment_sign_up.html', {
        'profile_image_form': profile_image_form,
        'profile_form': profile_form,
        'profile': comment.author,
        'form': form,
        'project': comment.page.project,
        'page': comment.page,
        'reply_to': reply_to,
        'comment': comment,
    }, context_instance=RequestContext(request))


@login_required
@organizer_required
def accept_sign_up(request, slug, comment_id, as_organizer=False):
    page = get_object_or_404(Page, project__slug=slug, slug='sign-up')
    project = page.project
    answer = page.comments.get(pk=comment_id)
    organizing = project.is_organizing(answer.author.user)
    participating = project.is_participating(answer.author.user)
    if answer.reply_to or organizing or participating or request.method != 'POST':
        return HttpResponseForbidden()
    participation = Participation(project=project, user=answer.author, organizing=as_organizer)
    participation.save()
    new_rel = Relationship(source=answer.author, target_project=project)
    try:
        new_rel.save()
    except IntegrityError:
        pass
    accept_content = detail_description_content = render_to_string(
            "content/accept_sign_up_comment.html",
            {'as_organizer': as_organizer})
    accept_comment = PageComment(content=accept_content, 
        author = request.user.get_profile(), page = page, reply_to = answer, 
        abs_reply_to = answer)
    accept_comment.save()
    if as_organizer:
        messages.success(request, _('Organizer added!'))
    else:
        messages.success(request, _('Participant added!'))
    return HttpResponseRedirect(answer.get_absolute_url())


@login_required
@participation_required
def page_index_up(request, slug, counter):
    #Page goes up in the sidebar index (page.index decreases)."""
    project = get_object_or_404(Project, slug=slug)
    try:
        counter = int(counter)
    except ValueError:
        raise Http404
    content_pages = Page.objects.filter(project__pk=project.pk, listed=True).order_by('index')
    if counter < 1 or content_pages.count() <= counter:
        raise Http404
    prev_page = content_pages[counter - 1]
    page = content_pages[counter]
    prev_page.index, page.index = page.index, prev_page.index
    page.save()
    prev_page.save()
    return HttpResponseRedirect(project.get_absolute_url() + '#tasks')


@login_required
@participation_required
def page_index_down(request, slug, counter):
    #Page goes down in the sidebar index (page.index increases). 
    project = get_object_or_404(Project, slug=slug)
    try:
        counter = int(counter)
    except ValueError:
        raise Http404
    content_pages = Page.objects.filter(project__pk=project.pk, listed=True, deleted=False).order_by('index')
    if counter < 0 or content_pages.count() - 1 <= counter:
        raise Http404
    next_page = content_pages[counter + 1]
    page = content_pages[counter]
    next_page.index, page.index = page.index, next_page.index
    page.save()
    next_page.save()
    return HttpResponseRedirect(project.get_absolute_url() + '#tasks')

@login_required
@participation_required
def link_index_up(request, slug, counter):
   #Link goes up in the sidebar index (link.index decreases).
    project = get_object_or_404(Project, slug=slug)
    try:
        counter = int(counter)
    except ValueError:
        raise Http404
    links = Link.objects.filter(project__pk=project.pk).order_by('index')
    if counter < 1 or links.count() <= counter:
        raise Http404
    prev_link = links[counter - 1]
    link = links[counter]
    prev_link.index, link.index = link.index, prev_link.index
    link.save()
    prev_link.save()
    return HttpResponseRedirect(project.get_absolute_url() + '#links')


@login_required
@participation_required
def link_index_down(request, slug, counter):
    #Link goes down in the sidebar index (link.index increases).
    project = get_object_or_404(Project, slug=slug)
    try:
        counter = int(counter)
    except ValueError:
        raise Http404
    links = Link.objects.filter(project__pk=project.pk).order_by('index')
    if counter < 0 or links.count() - 1 <= counter:
        raise Http404
    next_link = links[counter + 1]
    link = links[counter]
    next_link.index, link.index = link.index, next_link.index
    link.save()
    next_link.save()
    return HttpResponseRedirect(project.get_absolute_url() + '#links')

