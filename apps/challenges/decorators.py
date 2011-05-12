from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from challenges.models import Challenge, Submission


def challenge_owner_required(func):
    """ check that the current user is the challenge owner """

    def decorator(*args, **kwargs):
        request = args[0]
        challenge = get_object_or_404(Challenge, slug=kwargs['slug'])
        user = request.user.get_profile()

        if user != challenge.created_by:
            return HttpResponseForbidden(_("You can't decorate challenge"))
        return func(*args, **kwargs)
    return decorator


def submission_owner_required(func):
    """ check that the current user is the challenge response owner """

    def decorator(*args, **kwargs):
        request = args[0]
        submission = get_object_or_404(Submission,
                                       pk=kwargs['submission_id'])
        user = request.user.get_profile()

        if user != submission.created_by:
            return HttpResponseForbidden(_("You can't decorate submission"))
        return func(*args, **kwargs)
    return decorator
