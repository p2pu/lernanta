import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.contrib.sessions.models import Session

from l10n.urlresolvers import reverse
from drumbeat import messages
from users.decorators import login_required, secure_required
from preferences import forms
from preferences.models import get_notification_categories
from preferences.models import get_user_unsubscribes
from preferences.models import set_notification_subscription

log = logging.getLogger(__name__)

@secure_required
@login_required
def notifications(request):
    profile = request.user.get_profile()
    unsubscribes = get_user_unsubscribes(profile)

    subscriptions = []
    if request.user.is_superuser:
        subscriptions += [ ('Admin notifications', get_notification_categories()[1:3]) ]

    subscriptions += [ ('Notifications about', get_notification_categories()[3:]) ]

    user_courses = profile.get_current_projects()
    all_courses = user_courses['organizing'] + user_courses['participating'] + user_courses['following']
    sources = []
    for course in all_courses:
        if '/groups/' in course['url']:
            category = u'project-{0}'.format(course['id'])
        else:
            category = 'course-{0}'.format(course['id'])
        sources += [{'category': category, 'description': '{0}'.format(course['title'])} ]

    subscriptions += [(_('Notifications from'), sources)]

    if request.method == 'POST':
        for category in request.POST.keys():
            set_notification_subscription(profile, category, True)
        all_categories = get_notification_categories()[1:] + sources
        for category in [c['category'] for c in all_categories if c['category'] not in request.POST.keys()]:
            set_notification_subscription(profile, category, False)
        return HttpResponseRedirect(reverse('preferences_notifications'))

    context = {
        'domain': Site.objects.get_current().domain,
        'notifications_tab': True,
        'subscriptions': subscriptions,
        'unsubscribes': unsubscribes
    }

    return render_to_response('preferences/notifications.html', context,
                              context_instance=RequestContext(request))


@secure_required
@login_required
def email(request):
    profile = request.user.get_profile()
    email = profile.user.email
    if request.method == "POST":
        form = forms.EmailEditForm(profile.username, request.POST,
            request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user.email = profile.email
            profile.user.save()
            profile.confirmation_code = profile.generate_confirmation_code()
            profile.save()
            path = reverse('users_confirm_registration', kwargs={
                'username': profile.username,
                'token': profile.confirmation_code,
            })
            url = request.build_absolute_uri(path)
            profile.email_confirmation_code(url, new_user=False)
            msg1 = _('A link to confirm your email address was sent '
              'to %s.') % profile.email
            messages.info(request, msg1)
            form = forms.EmailEditForm(profile.username, instance=profile)
    else:
        form = forms.EmailEditForm(profile.username, instance=profile)

    if profile.confirmation_code and not form.is_bound:
        url = request.build_absolute_uri(reverse('users_confirm_resend'))
        msg2 = _('If you did not receive the confirmation email, make '
            'sure your email service did not mark it as "junk '
            'mail" or "spam". If you need to, you can have us '
            '<a href="%s">resend the confirmation message</a> '
            'to your email address.') % url
        messages.info(request, msg2, safe=True)

    return render_to_response('users/settings_email.html', {
        'profile': profile,
        'email': email,
        'form': form,
        'email_tab': True,
    }, context_instance=RequestContext(request))


@secure_required
@login_required
def password(request):
    profile = request.user.get_profile()
    if request.method == "POST":
        form = forms.PasswordEditForm(request.POST, request.FILES,
                                     instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.set_password(form.cleaned_data['password'])
            messages.success(request, _('Password updated'))
            profile.user = request.user
            profile.save()
        else:
            messages.error(request, _('There are errors in this form. Please '
                                      'correct them and resubmit.'))
    else:
        form = forms.PasswordEditForm(instance=profile)

    return render_to_response('users/settings_password.html', {
        'profile': profile,
        'form': form,
        'password_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def delete(request):
    profile = request.user.get_profile()
    current_projects = profile.get_current_projects()
    pending_projects = []
    if request.method == 'POST':
        if len(current_projects['organizing']) > 0:
            msg = _('You are the organizer of %s active courses. You need to archive these courses or remove yourself as organizer before you can delete your profile.')
            messages.error(request, msg % len(current_projects['organizing']))
            return HttpResponseRedirect(reverse('preferences_delete'))
        profile.deleted = True
        profile.user.is_active = False
        profile.save()
        profile.user.save()
        # logout the user on next access in user middleware.
        return HttpResponseRedirect(reverse('users_logout'))
    context = {
        'pending_projects': pending_projects,
        'delete_tab': True,
        'profile': profile
    }
    return render_to_response('users/settings_delete.html', context,
        context_instance=RequestContext(request))
