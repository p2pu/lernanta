import logging 
import json
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.contrib.auth.models import User
from urllib2 import urlopen, URLError, HTTPError
from urllib import urlencode

from utils import *

badge_getter = settings.MOZBADGES['badge_getter']
hub_uri = settings.MOZBADGES['hub']
get_awarded_badges = process_getter(badge_getter)

json_mime = 'application/json'
badge_mime = 'application/x-badge-manifest'


def retrieve_badge(request, identifier):
    """
    Gets the manifest for a specific badge based on identifier.
    See _b64badges() for how identifiers are determined
    """
    
    print 'getting badge: %s' % identifier
    try:
        data = json.loads(base64url_decode(str(identifier)))
        email, badge_id = data['email'], data['id']
        username = User.objects.get(email=email).username
        badge = get_awarded_badges(username).get(badge_id)
    except:
        raise Http404()
    
    response = {
        'spec': '0.1.0',
        'name': badge['name'],
        'evidence': badge['url'],
        'image': badge['image_url'],
        'recipient': email,
        'description': badge['description'],
        'template': badge['template'],
    }
    return HttpResponse(json.dumps(response), mimetype='application/x-badge-manifest')


def user_badges(request):
    badges = badge_urls(request)
    return HttpResponse(json.dumps(badges), mimetype=json_mime)
    

def send_badges(request):
    # changes state, should not be GETable.
    if not settings.DEBUG and not request.method == 'POST':
        return HttpResponse('GET not supported', status=501)
    
    # TODO: do a better job of defining API paths
    issue_path = "%s/badges/issue" % hub_uri
    user = request.user
    postdata = urlencode({'urls': json.dumps(badge_urls(request))})

    status = 200
    resp = {'status':'accepted'}
    
    try:
        hubresp = urlopen(issue_path, postdata)
    except HTTPError, e:
        # TODO: what do if the error is truly unexpected (server down)
        errors = json.loads(e.read())
        resp = {'status':'failure', 'errors': errors}
        status = 500
    except URLError, e:
        resp = {'status':'fatal', 'message': 'could not open connection to hub'}
        status = 500
    return HttpResponse(json.dumps(resp), mimetype=json_mime, status=status)

def badge_urls(request):
    """
    Gets a list of absolute urls for the badges belonging to the currently
    authenticated user. Outputs a json array.
    """
    badges = []
    user = request.user
    if user.is_authenticated():
        # TODO: don't hardcode first part of path?
        path = "/badges/%s.badge"
        absolute = request.build_absolute_uri
        badges = map(lambda a: absolute(path % a), _b64badges(user))
    return badges

def _b64badges(user):
    """
    Given a user id, will spit out the list of user's base64 encoded badge
    identifiers. Payload for base64 encoding is json string specifying email
    address and badge id ('tag').
    """
    badges = get_awarded_badges(user)
    email = User.objects.get(username=user).email
    urls = []
    for name in badges:
        raw_json = json.dumps({'email':email, 'id':name})
        urls.append(base64url_encode(raw_json))
    return urls
