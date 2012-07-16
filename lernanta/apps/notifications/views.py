from django import http
from django.views.decorators.csrf import csrf_exempt

from notifications.models import ResponseToken, post_notification_response
from users.models import UserProfile

import logging
log = logging.getLogger(__name__)

@csrf_exempt
def response(request):
    """ Web hook called when a response to a notification is received """

    log.debug("notifications.views.response")

    if not request.method == 'POST':
        raise http.Http404

    to_email = request.POST.get('to')
    from_email = request.POST.get('from')
    reply_text = request.POST.get('text')

    # clean up reply_text - original notification text should be removed by
    # module that sent the notification
    reply_text = reply_text.strip()
    if reply_text.startswith("['"):
        reply_text = reply_text[2:]
    if reply_text.endswith("']'"):
        reply_text = reply_text[:-2]
    
    # get response token from 'reply+token@reply.p2pu.org'
    token_text = None
    if to_email.find('+') != -1 and to_email.find('@') != -1:
        token_text = to_email[to_email.index('+')+1:to_email.index('@')]

    token = None
    try:
        token = ResponseToken.objects.get(response_token=token_text)
    except ResponseToken.DoesNotExist:
        log.error("Response token {0} does not exist".format(token_text))

    # convert 'User Name <email@server.com>' to 'email@server.com'
    if from_email.find('<') != -1 and from_email.find('>') != -1:
        from_email = from_email[from_email.index('<')+1:from_email.index('>')]

    user = None
    try:
        user = UserProfile.objects.get(email=from_email)
    except UserProfile.DoesNotExist:
        log.error(
            "Invalid user for response. User: {0}, Token: {1}".format(
                from_email, token_text
            )
        )

    if token and user and reply_text:
        # post to token.response_callback
        post_notification_response(token, user.email, reply_text)
    else:
        log.error("notifications.response: Invalid response")

    return http.HttpResponse(status=200)
