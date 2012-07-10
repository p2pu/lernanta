import logging

from django import http
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from l10n.urlresolvers import reverse
from drumbeat import messages
from users.decorators import login_required
from replies.models import PageComment
from replies.forms import CommentForm
from users.models import UserProfile
from replies import utils

log = logging.getLogger(__name__)

def show_comment(request, comment_id):
    comment = get_object_or_404(PageComment, id=comment_id)
    if comment.deleted:
        messages.error(request, _('This comment was deleted.'))
        if comment.can_edit(request.user):
            return http.HttpResponseRedirect(reverse('comment_restore',
                kwargs={'comment_id': comment.id}))
        else:
            page_url = comment.page_object.get_absolute_url()
            return http.HttpResponseRedirect(page_url)
    else:
        comment_url = comment.page_object.get_comment_url(comment,
            request.user)
        return http.HttpResponseRedirect(comment_url)


@login_required
def reply_comment(request, comment_id):
    reply_to = get_object_or_404(PageComment, id=comment_id)
    if reply_to.deleted:
        return http.HttpResponseRedirect(reply_to.get_absolute_url())
    can_reply = reply_to.page_object.can_comment(request.user,
        reply_to=reply_to)
    if not can_reply:
        messages.error(request, _('You can not reply to this comment.'))
        return http.HttpResponseRedirect(reply_to.get_absolute_url())
    user = request.user.get_profile()
    comment = None
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.page_object = reply_to.page_object
            comment.scope_object = reply_to.scope_object
            comment.author = user
            comment.reply_to = reply_to
            comment.abs_reply_to = reply_to.abs_reply_to or reply_to
            if 'show_preview' not in request.POST:
                comment.save()
                comment.send_comment_notification()
                messages.success(request, _('Comment posted!'))
                return http.HttpResponseRedirect(comment.get_absolute_url())
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        form = CommentForm()

    context = {
        'form': form,
        'scope_object': reply_to.scope_object,
        'page_object': reply_to.page_object,
        'reply_to': reply_to,
        'comment': comment,
        'create': True,
        'preview': ('show_preview' in request.POST),
    }

    return render_to_response('replies/comment_page.html', context,
        context_instance=RequestContext(request))


@login_required
def comment_page(request, page_model, page_app_label, page_pk,
        scope_model=None, scope_app_label=None, scope_pk=None):

    page_ct_cls = get_object_or_404(ContentType, model=page_model,
        app_label=page_app_label).model_class()
    page_object = get_object_or_404(page_ct_cls, pk=page_pk)

    scope_object = None
    if scope_model:
        scope_ct_cls = get_object_or_404(ContentType, model=scope_model,
            app_label=scope_app_label).model_class()
        scope_object = get_object_or_404(scope_ct_cls, pk=scope_pk)

    can_comment = page_object.can_comment(request.user)
    if not can_comment:
        msg = _('You can not post a comment at %s.')
        messages.error(request, msg % page_object)
        return http.HttpResponseRedirect(page_object.get_absolute_url())

    kwargs = {
        'page_app_label': page_app_label,
        'page_model': page_model,
        'page_pk': page_pk
    }
    if scope_object:
        kwargs.update({
            'scope_app_label': scope_app_label,
            'scope_model': scope_model,
            'scope_pk': scope_pk
        })

    new_comment_url = reverse('page_comment', kwargs=kwargs)
    user = request.user.get_profile()

    comment = None
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.page_object = page_object
            comment.scope_object = scope_object
            comment.author = user
            if 'show_preview' not in request.POST:
                comment.save()
                comment.send_comment_notification()
                messages.success(request, _('Comment posted!'))
                return http.HttpResponseRedirect(comment.get_absolute_url())
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        form = CommentForm()

    return render_to_response('replies/comment_page.html', {
        'form': form,
        'scope_object': scope_object,
        'page_object': page_object,
        'comment': comment,
        'create': True,
        'preview': ('show_preview' in request.POST),
        'new_comment_url': new_comment_url,
    }, context_instance=RequestContext(request))


@csrf_exempt
@require_POST
def comment_page_callback(request, page_model, page_app_label, page_pk,
        scope_model, scope_app_label, scope_pk):
    """ callback used when replying by email to an activity"""

    log.debug("replies.views.comment_page_callback")

    api_key = request.POST.get('api-key')
    if not api_key == settings.INTERNAL_API_KEY:
        log.error('Invalid API KEY used for internal API!')
        return http.HttpResponseForbidden()
    
    from_email = request.POST.get('from')
    reply_text = request.POST.get('text')
    reply_text = utils.extract_reply(reply_text)

    user = None
    try:
        user = UserProfile.objects.get(email=from_email)
    except UserProfile.DoesNotExist:
        log.error("Invalid user attempted reply: {0}".format(from_email))

    page_object = None
    try:
        page_ct_cls = ContentType.objects.get(model=page_model,
        app_label=page_app_label).model_class()
        page_object = page_ct_cls.objects.get(pk=page_pk)
    except:
        log.error("could not find page object")

    scope_object = None
    try:
        scope_ct_cls = ContentType.objects.get(model=scope_model,
            app_label=scope_app_label).model_class()
        scope_object = get_object_or_404(scope_ct_cls, pk=scope_pk)
    except:
        log.error("could not find scope object")

    if user and page_object and page_object.can_comment(user.user) and scope_object and reply_text:
        comment = PageComment(content=reply_text)
        comment.page_object = page_object
        comment.scope_object = scope_object
        comment.author = user
        comment.sent_by_email = True
        comment.save()

    return http.HttpResponse(status=200)


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(PageComment, id=comment_id)
    if not comment.can_edit(request.user):
        messages.error(request, _('You can not edit this comment.'))
        return http.HttpResponseRedirect(comment.get_absolute_url())
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            if 'show_preview' not in request.POST:
                comment.save()
                messages.success(request, _('Comment updated!'))
                return http.HttpResponseRedirect(comment.get_absolute_url())
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        form = CommentForm(instance=comment)
        
    return render_to_response('replies/comment_page.html', {
        'form': form,
        'comment': comment,
        'page_object': comment.page_object,
        'scope_object': comment.scope_object,
        'reply_to': comment.reply_to,
        'preview': ('show_preview' in request.POST),
    }, context_instance=RequestContext(request))


@login_required
def delete_restore_comment(request, comment_id):
    comment = get_object_or_404(PageComment, id=comment_id)
    if not comment.can_edit(request.user):
        if comment.deleted:
            msg = _('You can not restore this comment.')
        else:
            msg = _('You can not delete this comment.')
        messages.error(request, msg)
        return http.HttpResponseRedirect(comment.get_absolute_url())
    if request.method == 'POST':
        comment.deleted = not comment.deleted
        comment.save()
        if comment.deleted:
            msg = _('Comment deleted!')
        else:
            msg = _('Comment restored!')
        messages.success(request, msg)
        if comment.deleted:
            return http.HttpResponseRedirect(
                comment.page_object.get_absolute_url())
        else:
            return http.HttpResponseRedirect(comment.get_absolute_url())
    else:
        return render_to_response('replies/delete_restore_comment.html', {
            'comment': comment,
            'page_object': comment.page_object,
            'scope_object': comment.scope_object,
        }, context_instance=RequestContext(request))


@csrf_exempt
@require_POST
def email_reply(request, comment_id):
    """ handle a reply received via email """

    log.debug("replies:email_reply")

    api_key = request.POST.get('api-key')
    if not api_key == settings.INTERNAL_API_KEY:
        log.error('Invalid API KEY used for internal API!')
        return http.HttpResponseForbidden()
    
    from_email = request.POST.get('from')
    reply_text = request.POST.get('text')
    reply_text = utils.extract_reply(reply_text)
    
    comment = None
    try:
        comment = PageComment.objects.get(id=comment_id)
    except PageComment.DoesNotExist:
        log.error("Reply does not exist")

    user = None
    try:
        user = UserProfile.objects.get(email=from_email)
    except UserProfile.DoesNotExist:
        log.error("Invalid user attempted reply: {0}".format(from_email))

    if comment and user and reply_text and not comment.deleted:
        comment.reply(user, reply_text, True)

    return http.HttpResponse(status=200)
