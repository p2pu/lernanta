from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django import http
from django.utils.translation import ugettext as _

from pagination.views import get_pagination_context
from projects.models import Project
from users.decorators import login_required
from drumbeat import messages
from l10n.urlresolvers import reverse

from reviews.models import Review, Reviewer
from reviews.decorators import reviewer_required
from reviews.forms import ReviewForm


@login_required
@reviewer_required
def projects_reviews_list(request, toggled_reviewed=False):
    accepted_reviews = Review.objects.filter(
        accepted=True).values('project_id')
    new_projects = Project.objects.filter(under_development=False,
        archived=False, deleted=False, not_listed=False).exclude(
        id__in=accepted_reviews)
    reviewed_projects = Project.objects.filter(
        id__in=accepted_reviews)
    context = {
        'toggled_reviewed': toggled_reviewed,
        'show_new_page_url': reverse('reviews_show_new'),
        'show_reviewed_page_url': reverse('reviews_show_reviewed')
    }
    context.update(get_pagination_context(request, new_projects,
        24, prefix='new_'))
    context.update(get_pagination_context(request, reviewed_projects,
        24, prefix='reviewed_'))
    return render_to_response('reviews/projects_reviews_list.html',
        context, context_instance=RequestContext(request))


def show_new(request):
    return projects_reviews_list(request)


def show_reviewed(request):
    return projects_reviews_list(request, toggled_reviewed=True)


@login_required
@reviewer_required
def show_project_reviews(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render_to_response('reviews/show_project_reviews.html',
        {'project': project}, context_instance=RequestContext(request))


@login_required
@reviewer_required
def review_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    profile = request.user.get_profile()
    reviewer = Reviewer.objects.get(user=profile)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = project
            review.author = profile
            review.save()
            if reviewer.can_feature:
                project.community_featured = review.mark_featured
            if reviewer.can_delete:
                project.deleted = review.mark_deleted
            if reviewer.can_feature or reviewer.can_delete:
                project.save()
            review.send_notifications_i18n()
            messages.success(request, _('Review posted!'))
            return http.HttpResponseRedirect(review.get_absolute_url())
        else:
            messages.error(request, _('Please correct errors below.'))
    else:
        form = ReviewForm()
    context = {'form': form, 'project': project, 'reviewer': reviewer}
    return render_to_response('reviews/review_project.html',
        context, context_instance=RequestContext(request))
