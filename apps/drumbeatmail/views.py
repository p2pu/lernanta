import logging
import math
import datetime
import operator

from django import http
from django.db.models.fields.files import ImageFieldFile
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse
from drumbeat import messages
from drumbeatmail import forms
from messages.models import Message
from users.models import UserProfile
from users.decorators import login_required

log = logging.getLogger(__name__)

PAGE_SIZE = 10  # Number of messages to display on one page


def get_sorted_senders(user):
    """
    Helper function. Return a list of distinct senders, sorted by
    the number of messages received from them.
    """
    msgs = Message.objects.inbox_for(user).select_related('sender')
    senders = {}
    for msg in msgs:
        sender = msg.sender.get_profile()
        senders.setdefault(sender, 0)
        senders[sender] += 1
    return sorted(senders.iteritems(), key=operator.itemgetter(1))


def get_pagination_options(count, page_number):
    """
    Helper function. Calculate and return the number of pages and
    the start and end indices based on a total count and page number.
    """
    n_pages = int(math.ceil(count / float(PAGE_SIZE)))
    start = (page_number - 1) * PAGE_SIZE
    end = page_number * PAGE_SIZE
    return (n_pages, start, end)


def serialize(inbox, sent_view=False):
    """Serialize messages for xhr."""
    data = []
    for msg in inbox:
        sender = msg.sender
        if sent_view:
            sender = msg.recipient
        img = sender.get_profile().image_or_default()
        if isinstance(img, ImageFieldFile):
            img = img.name
        serialized = {
            'abuse_url': reverse('drumbeat_abuse', kwargs=dict(
                model='message', app_label='messages', pk=msg.id)),
            'reply_url': reverse('drumbeatmail_reply', kwargs=dict(
                message=msg.id)),
            'sender_url': sender.get_profile().get_absolute_url(),
            'sender_img': img,
            'sender_name': sender.get_profile().display_name,
            'subject': msg.subject,
            'body': msg.body,
            'sent_at': msg.sent_at.strftime('%b. %d, %Y, %I:%M %p').replace(
                'PM', 'p.m.').replace('AM', 'a.m.'),
        }
        if sent_view:
            del serialized['abuse_url']
            del serialized['reply_url']
        data.append(serialized)
    return simplejson.dumps(data)


def generic_inbox(request, query_method, query_args, page_number,
                  more_link_name, more_link_kwargs, redirect, filter=None,
                  sent_view=False):
    """
    Three views in this application render the inbox with different but
    very similar contexts. This is a helper function used to wrap that
    rendering and all of the pagination logic.

    ``request`` - The ``HttpRequest`` object associated with this request.
    ``query_method`` - A callable that will return a list of messages for
                       this view.
    ``query_args`` - A list of arguments for ``query_method``.
    ``page_number`` - The page number being rendered.
    ``more_link_name`` - A named URLconf to use for the more link.
    ``more_link_kwargs`` - Named arguments for the more link.
    ``redirect`` - A URL to redirect to for invalid page numbers.
    ``filter`` - Optional filter kwargs for ``query_method``.
    ``sent_view`` - Whether or not to render the outbox view or not. When
                    viewing the outbox, user icons are the recipient, not
                    the sender.
    """
    page_number = int(page_number)
    msgs = query_method(*query_args)
    if filter:
        msgs = msgs.filter(**filter)
    count = msgs.count()
    (n_pages, start, end) = get_pagination_options(count, page_number)

    if n_pages > 0 and page_number > n_pages:
        return http.HttpResponseRedirect(redirect)

    inbox = msgs.select_related('sender')[start:end]
    senders = get_sorted_senders(request.user)

    for msg in inbox:
        if not msg.read_at:
            msg.read_at = datetime.datetime.now()
            msg.save()

    if request.is_ajax():
        data = serialize(inbox, sent_view)
        return http.HttpResponse(data, 'application/json')

    page_number += 1
    more_link_kwargs['page_number'] = page_number
    more_link = reverse(more_link_name, kwargs=more_link_kwargs)
    return render_to_response('drumbeatmail/inbox.html', {
        'inbox': inbox,
        'senders': senders,
        'page_number': page_number,
        'n_pages': n_pages,
        'more_link': more_link,
        'sent_view': sent_view,
    }, context_instance=RequestContext(request))


@login_required
def inbox(request, page_number=1):
    func = Message.objects.inbox_for
    func_args = (request.user,)
    more_link_name = 'drumbeatmail_inbox_offset'
    return generic_inbox(
        request, func, func_args, page_number, more_link_name, {},
        reverse('drumbeatmail_inbox'))


@login_required
def inbox_filtered(request, filter, page_number=1):
    sender = get_object_or_404(UserProfile, username=filter)
    func = Message.objects.inbox_for
    func_args = (request.user,)
    redirect_url = reverse('drumbeatmail_inbox_filtered',
                           kwargs=dict(filter=filter))
    more_link_name = 'drumbeatmail_inbox_filtered_offset'
    more_link_kwargs = dict(filter=filter)
    return generic_inbox(
        request, func, func_args, page_number, more_link_name,
        more_link_kwargs, redirect_url, dict(sender=sender))


@login_required
def outbox(request, page_number=1):
    func = Message.objects.outbox_for
    func_args = (request.user,)
    more_link_name = 'drumbeatmail_outbox_offset'
    return generic_inbox(
        request, func, func_args, page_number, more_link_name, {},
        reverse('drumbeatmail_outbox'), sent_view=True)


@login_required
def reply(request, message):
    message = get_object_or_404(Message, id=message)
    if message.recipient != request.user:
        return http.HttpResponseForbidden(_("Can't send email"))
    if request.method == 'POST':
        form = forms.ComposeForm(data=request.POST,
                                 sender=request.user.get_profile())
        if form.is_valid():
            form.save(sender=request.user)
            messages.success(request, _('Message successfully sent.'))
            return http.HttpResponseRedirect(reverse('drumbeatmail_inbox'))
        else:
            messages.error(request, _('There was an error sending your message'
                                      '. Please try again.'))
    else:
        if not message.subject.startswith('Re: '):
            subject = 'Re: %s' % (message.subject,)
        else:
            subject = message.subject
        form = forms.ComposeForm(initial={
            'recipient': message.sender.get_profile().username,
            'subject': subject,
        })
    return render_to_response('drumbeatmail/reply.html', {
        'form': form,
        'message': message,
    }, context_instance=RequestContext(request))


@login_required
def compose(request, username=None):
    kwargs = {}
    if username:
        kwargs['sender'] = get_object_or_404(UserProfile, username=username)
    if request.method == 'POST':
        form = forms.ComposeForm(data=request.POST,
                                 sender=request.user.get_profile())
        if form.is_valid():
            form.save(sender=request.user)
            messages.success(request, _('Message successfully sent.'))
            return http.HttpResponseRedirect(reverse('drumbeatmail_inbox'))
        else:
            messages.error(request, _('There was an error sending your message'
                                      '. Please try again.'))
    else:
        form = forms.ComposeForm(initial={'recipient': username})
    kwargs['form'] = form
    return render_to_response('drumbeatmail/compose.html', kwargs,
                              context_instance=RequestContext(request))
