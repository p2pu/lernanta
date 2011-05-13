from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from projects.models import Project, Participation


def organizer_required(func):
    """
    Return a 403 response if the user is not organizing the project
    specified by the ``slug`` kwarg.
    """

    def decorator(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        if not project.is_organizing(request.user):
            return HttpResponseForbidden(_("You are not organizing this study group"))
        return func(*args, **kwargs)
    return decorator


def participation_required(func):
    """
    Return a 403 response if the user is not participating in the project
    specified by the ``slug`` kwarg.
    """
    def decorator(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        if not project.is_participating(request.user):
            return HttpResponseForbidden(_("You are not participating in this study group"))
        return func(*args, **kwargs)
    return decorator

