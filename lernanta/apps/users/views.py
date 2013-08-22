import logging
import urllib2
import datetime

from django import http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.utils.translation import ugettext as _
from django.utils.translation import activate, get_language
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.models import Site

from django_openid_auth import views as openid_views
from django_openid_auth.models import UserOpenID
from commonware.decorators import xframe_sameorigin
import tender_multipass

from l10n.urlresolvers import reverse
from l10n import locales
from urlparse import urlparse, urlunparse
from links.models import Link
from drumbeat import messages
from activity.models import Activity
from activity.views import filter_activities
from pagination.views import get_pagination_context
from badges.models import Award, get_awarded_badges

from users import forms
from users.models import UserProfile, create_profile, ProfileTag
from users.fields import UsernameField
from users.decorators import anonymous_only, login_required, secure_required
from users import drupal


log = logging.getLogger(__name__)


def render_openid_failure(request, message, status, template_name):
    if request.method == 'POST':
        form = forms.OpenIDForm(request.POST)
    else:
        form = forms.OpenIDForm()
    response = render_to_string(template_name, {
        'message': message,
        'form': form,
    }, context_instance=RequestContext(request))
    return http.HttpResponse(response, status=status)


def render_openid_registration_failure(request, message, status=403):
    return render_openid_failure(
        request, message, status, 'users/register_openid.html')


def render_openid_login_failure(request, message, status=403):
    return render_openid_failure(
        request, message, status, 'users/login_openid.html')


def _process_redirect(request):
    redirect_field_names = [REDIRECT_FIELD_NAME] + list(
        settings.SSO_REDIRECT_FIELD_NAMES)
    for field_name in redirect_field_names:
        if field_name in request.GET:
            request = _clean_redirect_url(request, field_name)
            request.session[REDIRECT_FIELD_NAME] = request.GET[REDIRECT_FIELD_NAME]
            break
    return request


def _clean_redirect_url(request, field_name):
    """Prevent us from redirecting unauthorized external urls."""
    gets = request.GET.copy()
    url = urllib2.unquote(gets[field_name])
    invalid_redirect = (url and not url.startswith('/oauth/') and '://' in url)
    for sso_redirect in settings.SSO_EXTERNAL_REDIRECTS:
        if url.startswith(sso_redirect):
            invalid_redirect = False
    if invalid_redirect:
        url = None
    gets[REDIRECT_FIELD_NAME] = url
    request.GET = gets
    return request


def _get_redirect_url(request):
    url = request.session.get(REDIRECT_FIELD_NAME, reverse('dashboard'))
    if not url or url == reverse('splash'):
        url = reverse('dashboard')
    if url:
        if REDIRECT_FIELD_NAME in request.session:
            del request.session[REDIRECT_FIELD_NAME]
        if not url.startswith('/') and '://' not in url:
            url = '/%s' % (url,)
    return url

def _after_login_redirect(redirect_url, profile):
    sso_url = None
    for sso_redirect in settings.SSO_EXTERNAL_REDIRECTS:
        if redirect_url.startswith(sso_redirect):
            sso_url = sso_redirect
    if not sso_url:
        return http.HttpResponseRedirect(redirect_url)
    site_key = settings.SSO_EXTERNAL_REDIRECTS[sso_url]['site_key']
    api_key = settings.SSO_EXTERNAL_REDIRECTS[sso_url]['api_key']
    multipass = tender_multipass.MultiPass(site_key, api_key)
    expires = datetime.datetime.now() + datetime.timedelta(days=14)
    data = {
        "unique_id": profile.username,
        "name": str(profile),
        "email": profile.email,
        "expires": expires.strftime("%Y-%m-%dT%H:%M"),
    }
    token = multipass.encode(data)
    return http.HttpResponseRedirect(redirect_url + '?sso=%s' % token)


def force_language_in_url(url, oldlang, newlang):
    """Rewrite url to use newlang instead of oldlang"""
    # Use when activate(newlang) is not enough
    # see https://docs.djangoproject.com/en/dev/topics/i18n/deployment/
    if '://' in url:
        return url
    if oldlang in locales.INTERNAL_MAP:
        oldlang = locales.INTERNAL_MAP[oldlang]
    p = urlparse(url)
    if (p.path.startswith('/' + oldlang + '/')):
        npath = p.path.replace('/' + oldlang + '/', '/' + newlang + '/', 1)
    else:
        npath = '/' + newlang + '/' + p.path
    return urlunparse([p.scheme, p.netloc, npath,
        p.params, p.query, p.fragment])


@secure_required
def login(request):
    """Log the user in. Lifted most of this code from zamboni."""

    request = _process_redirect(request)

    if request.user.is_authenticated():
        user = request.user.get_profile()
        redirect_url = _get_redirect_url(request)
        olang = get_language()
        force_language_in_url(
                redirect_url, olang, user.preflang)
        return _after_login_redirect(redirect_url, user)

    logout(request)

    dashboard_url = reverse('dashboard')
    redirect_field_value = request.session.get(
        REDIRECT_FIELD_NAME, dashboard_url) or dashboard_url
    try:
        redirect_field_value = urllib2.quote(redirect_field_value)
    except KeyError:
        # Unicode Issue
        pass
    extra_context = {
        'redirect_field_name': REDIRECT_FIELD_NAME,
        'redirect_field_value': redirect_field_value,
    }

    r = auth_views.login(request, template_name='users/signin.html',
                         authentication_form=forms.AuthenticationForm,
                         extra_context=extra_context)

    if isinstance(r, http.HttpResponseRedirect):
        user = request.user.get_profile()

        if request.POST.get('remember_me', None):
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            log.debug(u'User signed in with remember_me option')

        olang = get_language()
        activate(user.preflang)
        redirect_url = _get_redirect_url(request)
        if redirect_url:
            redirect_url = force_language_in_url(
                redirect_url, olang, user.preflang)
            return _after_login_redirect(redirect_url, user)

    elif request.method == 'POST':
        messages.error(request, _('Incorrect username, email or password.'))
        # run through auth_views.login again to render template with messages.
        r = auth_views.login(request, template_name='users/signin.html',
                         authentication_form=forms.AuthenticationForm)

    return r


@secure_required
@anonymous_only
def login_openid(request):
    if request.method == 'POST':
        return openid_views.login_begin(
            request,
            template_name='users/login_openid.html',
            form_class=forms.OpenIDForm,
            login_complete_view='users_login_openid_complete')
    else:
        form = forms.OpenIDForm()
    return render_to_response('users/login_openid.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@anonymous_only
@csrf_exempt
def login_openid_complete(request):
    setattr(settings, 'OPENID_CREATE_USERS', False)
    r = openid_views.login_complete(
        request, render_failure=render_openid_login_failure)
    if isinstance(r, http.HttpResponseRedirect):
        try:
            user = request.user.get_profile()
        except UserProfile.DoesNotExist:
            user = request.user
            username = ''
            if user.username[:10] != 'openiduser':
                username = user.username
            form = forms.CreateProfileForm(initial={
                'full_name': ' '.join((user.first_name, user.last_name)),
                'email': user.email,
                'username': username,
            })
            return render_to_response('dashboard/setup_profile.html', {
                'form': form,
            }, context_instance=RequestContext(request))

        redirect_url = _get_redirect_url(request)
        if redirect_url:
            return http.HttpResponseRedirect(redirect_url)

    return r


@login_required(profile_required=False)
def logout(request):
    """Destroy user session."""
    mark_registered = request.user.is_authenticated()
    auth.logout(request)
    if mark_registered:
        request.session['mark_registered'] = True
    return http.HttpResponseRedirect(reverse('home'))


@secure_required
@anonymous_only
def register(request):
    """Present user registration form and handle registrations."""

    request = _process_redirect(request)

    if request.method == 'POST':
        form = forms.RegisterForm(data=request.POST)

        if form.is_valid():
            django_user = form.save(commit=False)
            user = create_profile(django_user)
            user.set_password(form.cleaned_data['password'])
            user.generate_confirmation_code()
            user.full_name = form.cleaned_data['full_name']
            user.preflang = form.cleaned_data['preflang']
            user.save()

            log.info(u"Registered new account for user (%s)", user)

            messages.success(request, _('Congratulations! Your user account '
                                        'was successfully created.'))
            path = reverse('users_confirm_registration', kwargs={
                'username': user.username,
                'token': user.confirmation_code,
            })
            url = request.build_absolute_uri(path)
            user.email_confirmation_code(url)
            msg = _('Thanks! We have sent an email to {0} with '
                    'instructions for completing your '
                    'registration.').format(user.email)
            messages.info(request, msg)
            response = login(request)
            request.session['send_registration_event'] = True
            return response
        else:
            messages.error(request, _('There are errors in this form. Please '
                                      'correct them and resubmit.'))
    else:
        form = forms.RegisterForm()

    redirect_field_value = request.session.get(
        REDIRECT_FIELD_NAME, reverse('dashboard'))

    return render_to_response('users/register.html', {
        'form': form,
        'domain': Site.objects.get_current().domain,
        'redirect_field_name': REDIRECT_FIELD_NAME,
        'redirect_field_value': urllib2.quote(redirect_field_value),
    }, context_instance=RequestContext(request))


@secure_required
@anonymous_only
def register_openid(request):
    if request.method == 'POST':
        r = openid_views.login_begin(
            request,
            template_name='users/register_openid.html',
            form_class=forms.OpenIDForm,
            login_complete_view='users_register_openid_complete')
        return r
    else:
        form = forms.OpenIDForm()
    return render_to_response('users/register_openid.html', {
        'form': form,
    }, context_instance=RequestContext(request))


@anonymous_only
@csrf_exempt
def register_openid_complete(request):
    setattr(settings, 'OPENID_CREATE_USERS', True)
    return openid_views.login_complete(
        request, render_failure=render_openid_registration_failure)


def user_list(request):
    """Display a list of users on the site. Featured, new and active."""
    featured = UserProfile.objects.filter(deleted=False, featured=True)
    recent = UserProfile.objects.filter(deleted=False).order_by(
        '-created_on')[:20]
    popular = UserProfile.objects.get_popular(limit=20)
    return render_to_response('users/user_list.html', {
        'featured': featured,
        'recent': recent,
        'popular': popular,
    }, context_instance=RequestContext(request))


def user_tagged_list(request, tag_slug):
    """Display a list of users that are tagged with the tag and tag type. """
    tag = get_object_or_404(ProfileTag, slug=tag_slug)
    users = UserProfile.objects.filter(deleted=False, tags__slug=tag_slug)
    return render_to_response('users/user_list.html', {
        'tagged': users,
        'tag': tag,
    }, context_instance=RequestContext(request))


def confirm_registration(request, token, username):
    """Confirm a users registration."""
    profile = get_object_or_404(UserProfile, username=username)
    if profile.confirmation_code != token:
        messages.error(
            request,
           _('Hmm, that doesn\'t look like the correct confirmation code'))
        log.info('Email address confirmation failed for %s' % (profile,))
        return http.HttpResponseRedirect(reverse('users_login'))
    profile.confirmation_code = ''
    profile.save()
    profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth_login(request, profile.user)
    messages.success(request, _('Success! You have verified your email address.'))
    return http.HttpResponseRedirect(reverse('dashboard'))


@login_required
def confirm_resend(request):
    """Resend a confirmation code."""
    profile = request.user.get_profile()
    if profile.confirmation_code:
        path = reverse('users_confirm_registration', kwargs={
            'username': profile.username,
            'token': profile.confirmation_code,
        })
        url = request.build_absolute_uri(path)
        profile.email_confirmation_code(url, new_user=False)
        msg = _('A link to confirm your email address was sent '
              'to %s.')
        messages.info(request, msg % profile.email)
    return http.HttpResponseRedirect(reverse('preferences_email'))


def profile_view(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    if profile.deleted:
        messages.error(request, _('This user account was deleted.'))
        return http.HttpResponseRedirect(reverse('users_user_list'))

    activities = Activity.objects.for_user(profile)
    activities = filter_activities(request, activities)
    context = {
        'profile': profile,
        'profile_view': True,
        'domain': Site.objects.get_current().domain,
    }
    context.update(get_pagination_context(request, activities))
    return render_to_response('users/profile.html', context,
        context_instance=RequestContext(request))


@login_required(profile_required=False)
@require_http_methods(['POST'])
def profile_create(request):
    try:
        request.user.get_profile()
        return http.HttpResponseRedirect(reverse('dashboard'))
    except UserProfile.DoesNotExist:
        pass
    form = forms.CreateProfileForm(request.POST)
    if form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.id = profile.user.id
        profile.user.email = profile.email
        profile.user.save()
        profile.confirmation_code = profile.generate_confirmation_code()
        profile.save()
        path = reverse('users_confirm_registration', kwargs={
            'username': profile.username,
            'token': profile.confirmation_code,
        })
        url = request.build_absolute_uri(path)
        profile.email_confirmation_code(url)
        msg = _('Thanks! We have sent an email to %s with '
                'instructions for completing your '
                'registration.') % profile.email
        messages.info(request, msg)
        request.session['send_registration_event'] = True
        return http.HttpResponseRedirect(reverse('dashboard'))
    else:
        messages.error(request, _('There are errors in this form. Please '
                                      'correct them and resubmit.'))
    return render_to_response('dashboard/setup_profile.html', {
        'form': form,
        'domain': Site.objects.get_current().domain,
    }, context_instance=RequestContext(request))


@login_required
def profile_edit(request):
    profile = request.user.get_profile()
    if request.method == 'POST':
        form = forms.ProfileEditForm(request.POST, request.FILES,
                                     instance=profile)
        if form.is_valid():
            olang = get_language()
            activate(profile.preflang)
            messages.success(request, _('Profile updated'))
            form.save()
            next = reverse('users_profile_edit')
            next = force_language_in_url(next, olang, profile.preflang)
            return http.HttpResponseRedirect(next)
        else:
            messages.error(request, _('There were problems updating your '
                                      'profile. Please correct the problems '
                                      'and submit again.'))
    else:
        form = forms.ProfileEditForm(instance=profile)

    return render_to_response('users/profile_edit_main.html', {
        'profile': profile,
        'profile_form': form,
        'general_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def profile_edit_openids(request):
    profile = request.user.get_profile()
    if request.method == 'POST':
        return openid_views.login_begin(
            request,
            template_name='users/profile_edit_openids.html',
            form_class=forms.OpenIDForm,
            login_complete_view='users_profile_edit_openids_complete')
    else:
        form = forms.OpenIDForm()
    openids = UserOpenID.objects.filter(user=request.user)
    return render_to_response('users/profile_edit_openids.html', {
        'profile': profile,
        'form': form,
        'openids': openids,
        'openids_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@csrf_exempt
def profile_edit_openids_complete(request):
    openid_response = openid_views.parse_openid_response(request)
    yours_msg = _('The identity %s has already been claimed by you.')
    theirs_msg = _('The identity %s has already been claimed by another user.')
    if openid_response:
        if openid_response.status == openid_views.SUCCESS:
            url = openid_response.identity_url
            try:
                user_openid = UserOpenID.objects.get(
                    claimed_id__exact=url)
            except UserOpenID.DoesNotExist:
                user_openid = UserOpenID(user=request.user,
                claimed_id=openid_response.identity_url,
                display_id=openid_response.endpoint.getDisplayIdentifier())
                user_openid.save()
                messages.info(request,
                    _('The identity %s has been saved.') % url)
            else:
                if user_openid.user == request.user:
                    messages.error(request, yours_msg % url)
                else:
                    messages.error(request, theirs_msg % url)
        elif openid_response.status == openid_views.FAILURE:
            messages.error(request, _('OpenID authentication failed: %s') %
                openid_response.message)
        elif openid_response.status == openid_views.CANCEL:
            return messages.error(request, _('Authentication cancelled.'))
        else:
            return messages.error(
                _('Unknown OpenID response type: %r') % openid_response.status)
    else:
        return messages.error(_('This is an OpenID relying party endpoint.'))
    return http.HttpResponseRedirect(reverse('users_profile_edit_openids'))


@login_required
def profile_edit_openids_delete(request, openid_pk):
    if request.method == 'POST':
        openid = get_object_or_404(UserOpenID, pk=openid_pk)
        if openid.user != request.user:
            return http.HttpResponseForbidden(_("You can't edit this openid"))
        openid.delete()
        messages.success(request, _('The openid was deleted.'))
    return http.HttpResponseRedirect(reverse('users_profile_edit_openids'))


@login_required
@xframe_sameorigin
@require_http_methods(['POST'])
def profile_edit_image_async(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    form = forms.ProfileImageForm(request.POST, request.FILES,
                                  instance=profile)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.image.name,
        }))
    log.error('Error uploading image:%s' % form.errors)
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@login_required
def profile_edit_image(request):
    profile = request.user.get_profile()

    if request.method == 'POST':
        form = forms.ProfileImageForm(request.POST, request.FILES,
                                      instance=profile)
        if form.is_valid():
            messages.success(request, _('Profile image updated'))
            form.save()
            return http.HttpResponseRedirect(
                reverse('users_profile_edit_image'))
        else:
            messages.error(request, _('There was an error uploading '
                                      'your image.'))
    else:
        return http.HttpResponseRedirect(reverse('users_profile_edit'))


@login_required
def badges_manage(request):
    profile = request.user.get_profile()
    badges_help_url = "http://help.p2pu.org/kb/learning/what-are-badges"
    has_badges = get_awarded_badges(profile.user)
    badges_url = reverse('badges_list')
    context = {
        'profile': profile,
        'obi_url': settings.MOZBADGES['hub'],
        'badges_help_url': badges_help_url,
        'badges_url': badges_url,
        'has_badges': has_badges,
        'badges_tab': True,
    }
    return render_to_response('badges/profile_badges_manage.html',
        context, context_instance=RequestContext(request))


@login_required
def profile_edit_links(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = forms.ProfileLinksForm(request.POST)
        if form.is_valid():
            messages.success(request, _('Profile link added.'))
            link = form.save(commit=False)
            log.debug("User instance: %s" % (profile.user,))
            link.user = profile
            link.save()
            return http.HttpResponseRedirect(
                reverse('users_profile_edit_links'),
            )
        else:
            messages.error(request, _('There was an error saving '
                                      'your link.'))
    else:
        form = forms.ProfileLinksForm()
    links = Link.objects.select_related('subscription').filter(
        user=profile, project__isnull=True)

    return render_to_response('users/profile_edit_links.html', {
        'profile': profile,
        'form': form,
        'links': links,
        'link_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def profile_edit_links_edit(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    form = forms.ProfileLinksForm(request.POST or None, instance=link)
    profile = get_object_or_404(UserProfile, user=request.user)

    if form.is_valid():
        link = form.save(commit=False)
        link.user = profile
        messages.success(request, _('Profile link updated'))
        link.save()
        return http.HttpResponseRedirect(reverse('users_profile_edit_links'),)

    else:
        form = forms.ProfileLinksForm(instance=link)

    return render_to_response('users/profile_edit_links_edit.html', {
        'profile': profile,
        'form': form,
        'link': link,
        'link_tab': True,
    }, context_instance=RequestContext(request))


@login_required
def profile_edit_links_delete(request, link):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, user=request.user)
        link = get_object_or_404(Link, pk=link)
        if link.user != profile:
            return http.HttpResponseForbidden(_("You can't edit this link"))
        link.delete()
        messages.success(request, _('The link was deleted.'))
    return http.HttpResponseRedirect(reverse('users_profile_edit_links'))


@login_required
def link_index_up(request, counter):
    profile = get_object_or_404(UserProfile, user=request.user)
   #Link goes up in the sidebar index (link.index decreases).
    try:
        counter = int(counter)
    except ValueError:
        raise http.Http404
    links = Link.objects.filter(user=profile,
        project__isnull=True).order_by('index')
    if counter < 1 or links.count() <= counter:
        raise http.Http404
    prev_link = links[counter - 1]
    link = links[counter]
    prev_link.index, link.index = link.index, prev_link.index
    link.save()
    prev_link.save()
    return http.HttpResponseRedirect(profile.get_absolute_url() + '#links')


@login_required
def link_index_down(request, counter):
    profile = get_object_or_404(UserProfile, user=request.user)
    #Link goes down in the sidebar index (link.index increases).
    try:
        counter = int(counter)
    except ValueError:
        raise http.Http404
    links = Link.objects.filter(user=profile,
        project__isnull=True).order_by('index')
    if counter < 0 or links.count() - 1 <= counter:
        raise http.Http404
    next_link = links[counter + 1]
    link = links[counter]
    next_link.index, link.index = link.index, next_link.index
    link.save()
    next_link.save()
    return http.HttpResponseRedirect(profile.get_absolute_url() + '#links')


def check_username(request):
    """Validate a username and check for uniqueness."""
    username = request.GET.get('username', None)
    f = UsernameField()
    try:
        f.clean(username)
    except ValidationError:
        return http.HttpResponse()
    try:
        UserProfile.objects.get(username=username)
        return http.HttpResponse()
    except UserProfile.DoesNotExist:
        if drupal.get_user(username):
            return http.HttpResponse()
    return http.HttpResponse(status=404)


@login_required
def following(request):
    user = request.user.get_profile()
    term = request.GET.get('term', '').lower()
    usernames = [u.username for u in user.following()
                 if term in u.username.lower() or
                 term in u.full_name.lower()]
    return http.HttpResponse(simplejson.dumps(usernames),
                             mimetype='application/json')
