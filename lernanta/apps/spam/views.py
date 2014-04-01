from django.shortcuts import render_to_response
from django import http
from django.template import RequestContext
from django.utils.translation import ugettext as _

from drumbeat import messages
from l10n.urlresolvers import reverse
from users.decorators import login_required
from apps.spam.models import handle_spam_user

@login_required
def delete_spammer(request, username):
    if not request.user.is_superuser:
        return http.HttpResponseForbidden(_("Nice try, ask an admin to delete this user."))
    if request.method == 'POST':
        handle_spam_user(username)
        messages.success(request, _('Deleted spam user!'))
        return http.HttpResponseRedirect(reverse('users_user_list'))

    # display confirmation page
    context = { 'username': username }
    return render_to_response('spam/user_delete_confirmation.html',
        context, context_instance=RequestContext(request)
    )

