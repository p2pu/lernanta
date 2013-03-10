from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(r'^missing_redirect_uri/?$', 'oauthprovider.views.missing_redirect_uri',
        name='oauth_missing_redirect_uri'),

    url(r'^authorize/?$', 'oauthprovider.views.authorize',
        name='oauth_authorize'),

    url(r'^token/?$', 'oauth2app.token.handler',
        name='oauth_token_handler'),

    url(r'^whoami/$', 'oauthprovider.views.whoami',
        name='oauth_test'),
)
