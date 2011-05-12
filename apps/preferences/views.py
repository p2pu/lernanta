import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site

from l10n.urlresolvers import reverse
from drumbeat import messages
from users.decorators import login_required
from preferences import forms
from preferences.models import AccountPreferences
from users.models import UserProfile

log = logging.getLogger(__name__)


@login_required
def settings(request):
    profile = request.user.get_profile()
    participations = profile.participations.filter(left_on__isnull=True, organizing=False)
    if request.method == 'POST':
        for key in AccountPreferences.preferences:
            if key in request.POST and request.POST[key] == 'on':
                AccountPreferences.objects.filter(
                    user=profile, key=key).delete()
            else:
                AccountPreferences(
                    user=profile, key=key, value=1).save()
        for participation in participations:
            key = 'no_updates_%s' % participation.project.slug
            if key in request.POST and request.POST[key] == 'on':
                participation.no_updates = False
            else:
                participation.no_updates = True
            key = 'no_wall_updates_%s' % participation.project.slug
            if key in request.POST and request.POST[key] == 'on':
                participation.no_wall_updates = False
            else:
                participation.no_wall_updates = True
            participation.save()
        messages.success(
            request,
            _("Thank you, your settings have been saved."))
        return HttpResponseRedirect(reverse('preferences_settings'))
    preferences = AccountPreferences.objects.filter(
        user=request.user.get_profile())
    prefs = {'domain': Site.objects.get_current().domain, 'participations': participations}
    for preference in preferences:
        log.debug("%s => %s" % (preference.key, preference.value))
        prefs[preference.key] = preference.value
    return render_to_response('preferences/settings_notifications.html', prefs,
                              context_instance=RequestContext(request))

@login_required
def email(request):
    profile = request.user.get_profile()
    email = profile.user.email
    if request.method == "POST":
        form = forms.EmailEditForm(profile.username, request.POST, request.FILES,
                                     instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            messages.success(request, _('Email updated'))
            profile.user.email = profile.email
            profile.user.save()
            profile.save()
    else:
        form = forms.EmailEditForm(profile.username, instance=profile)

    return render_to_response('preferences/settings_email.html', {
        'email': email,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def password(request):
    profile = request.user.get_profile()
    password = ""
    password_confirm = ""
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

    return render_to_response('preferences/settings_password.html', {
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request):
    return HttpResponseRedirect(reverse('preferences_settings'))
    if request.method == 'POST':
        profile = request.user.get_profile()
        profile.user.delete()
        profile.delete()
        return HttpResponseRedirect(reverse('users_logout'))
    return render_to_response('preferences/settings_delete.html', {
    }, context_instance=RequestContext(request))
