from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

from users.decorators import login_required
from oauth2app.authorize import Authorizer, MissingRedirectURI, AuthorizationException
from oauth2app.authenticate import JSONAuthenticator, AuthenticationException


class AuthorizeForm(forms.Form):
    pass


def whoami(request):
    """Test authentication"""
    authenticator = JSONAuthenticator()
    try:
        authenticator.validate(request)
    except AuthenticationException:
        return authenticator.error_response()

    return authenticator.response({"user": authenticator.access_token.user.username})


@login_required
def missing_redirect_uri(request):
    return render_to_response('oauthprovider/missing_redirect_uri.html', {},
                              context_instance=RequestContext(request))

@login_required
def authorize(request):
    authorizer = Authorizer()

    try:
        authorizer.validate(request)
    except MissingRedirectURI, e:
        return HttpResponseRedirect(reverse('oauth_missing_redirect_uri'))
    except AuthorizationException, e:
        return authorizer.error_redirect()

    if request.method == 'GET':
        return render_to_response('oauthprovider/authorize.html', {
            'form': AuthorizeForm(),
            'form_action': '%s?%s' % (reverse('oauth_authorize'), authorizer.query_string)
        }, context_instance=RequestContext(request))
    elif request.method == 'POST':
        form = AuthorizeForm(request.POST)
        if form.is_valid():
            if request.POST.get('connect') == "on":
                return authorizer.grant_redirect()
            else:
                return authorizer.error_redirect()
    return authorizer.error_redirect()
