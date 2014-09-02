from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from l10n.urlresolvers import reverse
from drumbeat import messages
from projects.models import Project
from learn.templatetags.learn_tags import learn_default


def deprecated(func):
    """
    Show a deprecated warning for courses
    """
    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        msg = _('This course will become read-only in the near future. Tell us at <a href="http://community.p2pu.org/category/tech">community.p2pu.org</a> if that is a problem.')
        messages.warning(request, msg, safe=True)
        return func(*args, **kwargs)
    return decorated



def organizer_required(func):
    """
    Return a 403 response if the user is not organizing the project
    specified by the ``slug`` kwarg.
    """

    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        if not project.is_organizing(request.user):
            msg = _("You are not organizing this %s.")
            return HttpResponseForbidden(msg % project.kind.lower())
        return func(*args, **kwargs)
    return decorated


def participation_required(func):
    """
    Return a 403 response if the user is not participating in the project
    specified by the ``slug`` kwarg.
    """
    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        if not project.is_participating(request.user):
            msg = _("You are not participating in this %s.")
            return HttpResponseForbidden(msg % project.kind.lower())
        return func(*args, **kwargs)
    return decorated


def can_view_metric_detail(func):
    """
    Limited people can see the detailed metrics.
    """
    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        metric_csv_permissions = project.get_metrics_permissions(
            request.user)
        if not metric_csv_permissions:
            msg = _("You are not authorized to view the detailed statistics.")
            return HttpResponseForbidden(msg)
        return func(*args, **kwargs)
    return decorated


def can_view_metric_overview(func):
    """
    Allow certain people to view metrics of courses for the dark launch/slow
    rollout of this feature.
    """
    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        metric_permissions = project.get_metrics_permissions(
            request.user)
        if not metric_permissions:
            msg = _("You aren't authorized to view the statistics' overview.")
            return HttpResponseForbidden(msg)
        return func(*args, **kwargs)
    return decorated


def restrict_project_kind(*kinds):
    """Do not allow the access to this view if the project kind is not
    one of the given kinds."""
    def decorator(func):
        def decorated(*args, **kwargs):
            project = kwargs['slug']
            project = get_object_or_404(Project, slug=project)
            if not project.category in kinds:
                msg = _("This page is not accesible on a %s.")
                return HttpResponseForbidden(msg % project.kind.lower())
            return func(*args, **kwargs)
        return decorated
    return decorator


def hide_deleted_projects(func):
    """
    Return a redirect with a message if the project
    specified by the ``slug`` kwarg was deleted.
    """

    def decorated(*args, **kwargs):
        request = args[0]
        project = kwargs['slug']
        project = get_object_or_404(Project, slug=project)
        if project.deleted:
            messages.error(request, _('This %s was deleted.') % project.kind)
            return HttpResponseRedirect(learn_default())
        return func(*args, **kwargs)
    return decorated
