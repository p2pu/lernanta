from django import template

from pagination.views import get_pagination_context

from badges.models import Submission

register = template.Library()


def give_badge_action(project, peer):
    project_badges = project.get_badges_peers_can_give()
    context = {'badges': project_badges, 'peer': peer}
    return context

register.inclusion_tag('badges/_give_badge_action.html')(
    give_badge_action)


def badge_submissions(request, pending_page_url, awarded_page_url,
        mine_page_url, toggled_awards, toggled_mine, badge=None):
    pending_submissions = Submission.objects.filter(author__deleted=False, pending=True)
    awarded_submissions = Submission.objects.filter(author__deleted=False, pending=False)
    if badge:
        pending_submissions = pending_submissions.filter(badge=badge)
        awarded_submissions = awarded_submissions.filter(badge=badge)
    show_my_submissions_tab = False
    my_submissions = Submission.objects.none()
    if request.user.is_authenticated():
        show_my_submissions_tab = True
        my_submissions = Submission.objects.filter(
            author=request.user.get_profile())
        if badge:
            my_submissions = my_submissions.filter(badge=badge)
    context = {
        'request': request,
        'badge': badge,
        'show_my_submissions_tab': show_my_submissions_tab,
        'pending_page_url': pending_page_url,
        'awarded_page_url': awarded_page_url,
        'mine_page_url': mine_page_url,
        'toggled_awards': toggled_awards,
        'toggled_mine': toggled_mine,
    }
    context.update(get_pagination_context(request, pending_submissions,
        24, prefix='pending_submissions_'))
    context.update(get_pagination_context(request, awarded_submissions,
        24, prefix='awarded_submissions_'))
    context.update(get_pagination_context(request, my_submissions,
        24, prefix='my_submissions_'))
    return context

register.inclusion_tag('badges/_submissions_list.html')(
    badge_submissions)


def review_submission_action(request, submission):
    badge = submission.badge
    can_review_submission = badge.can_review_submission(
        submission, request.user)
    context = {
        'request': request,
        'submission': submission,
        'can_review_submission': can_review_submission,
    }
    return context

register.inclusion_tag('badges/_review_submission_action.html')(
    review_submission_action)
