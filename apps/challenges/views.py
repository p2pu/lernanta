from datetime import datetime
import logging

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.utils import IntegrityError
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render_to_response
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.template.defaultfilters import truncatewords
from django.views.decorators.http import require_http_methods

from commonware.decorators import xframe_sameorigin

from challenges.models import Challenge, Submission, Judge, VoterDetails
from challenges.forms import (ChallengeForm, ChallengeImageForm,
                              SubmissionSummaryForm, SubmissionForm,
                              SubmissionDescriptionForm,
                              JudgeForm, VoterDetailsForm)
from challenges.decorators import (challenge_owner_required,
                                   submission_owner_required)
from projects.models import Project

from drumbeat import messages
from users.decorators import login_required
from voting.models import Vote

log = logging.getLogger(__name__)


@login_required
def create_challenge(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.slug != 'mojo':
        return HttpResponseForbidden(_("You can't create challenge"))

    user = request.user.get_profile()

    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = user
            challenge.project = project
            challenge.save()

            messages.success(request,
                             _('Your new challenge has been created.'))
            return HttpResponseRedirect(reverse('challenges_show', kwargs={
                'slug': challenge.slug,
                }))
        else:
            messages.error(request, _('Unable to create your challenge.'))
    else:
        form = ChallengeForm()

    context = {
        'form': form,
        'project': project,
    }
    return render_to_response('challenges/challenge_edit_summary.html',
                              context,
                              context_instance=RequestContext(request))


@login_required
@challenge_owner_required
def edit_challenge(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    user = request.user.get_profile()

    if user != challenge.created_by:
        return HttpResponseForbidden(_("You can't edit challenge"))

    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            form.save()
            messages.success(request, _('Challenge updated!'))
            return HttpResponseRedirect(reverse('challenges_show', kwargs={
                'slug': challenge.slug,
                }))
        else:
            messages.error(request, _('Unable to update your challenge.'))
    else:
        form = ChallengeForm(instance=challenge)

    context = {
        'form': form,
        'project': challenge.project,
        'challenge': challenge,
    }

    return render_to_response('challenges/challenge_edit_summary.html',
                              context,
                              context_instance=RequestContext(request))


@login_required
@xframe_sameorigin
@require_http_methods(['POST'])
@challenge_owner_required
def edit_challenge_image_async(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    form = ChallengeImageForm(request.POST, request.FILES, instance=challenge)
    if form.is_valid():
        instance = form.save()
        return HttpResponse(simplejson.dumps({
            'filename': instance.image.name,
        }))
    return HttpResponse(simplejson.dumps({
        'error': _('There was an error uploading your image.'),
    }))


@login_required
@challenge_owner_required
def edit_challenge_image(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)

    if request.method == "POST":
        form = ChallengeImageForm(
            request.POST, request.FILES, instance=challenge)
        if form.is_valid():
            messages.success(request, _('Challenge image updated'))
            form.save()
            return HttpResponseRedirect(
                reverse('challenges_edit_image', kwargs={
                    'slug': challenge.slug,
                }))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = ChallengeImageForm(instance=challenge)

    context = {
        'form': form,
        'challenge': challenge,
    }

    return render_to_response('challenges/challenge_edit_image.html', context,
                              context_instance=RequestContext(request))


def show_challenge(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)

    qn = connection.ops.quote_name
    ctype = ContentType.objects.get_for_model(Submission)

    submission_set = challenge.submission_set.extra(select={'score': """
        SELECT SUM(vote)
        FROM %s
        WHERE content_type_id = %s
        AND object_id = %s.id
        """ % (qn(Vote._meta.db_table), ctype.id,
               qn(Submission._meta.db_table))
        },
        order_by=['-score']
    )
    paginator = Paginator(submission_set, 10)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        submissions = paginator.page(page)
    except (EmptyPage, InvalidPage):
        submissions = paginator.page(paginator.num_pages)

    form = SubmissionSummaryForm()
    remaining = challenge.end_date - datetime.now()

    try:
        profile = request.user.get_profile()
    except:
        profile = None

    context = {
        'challenge': challenge,
        'submissions': submissions,
        'form': form,
        'profile': profile,
        'remaining': remaining,
    }

    return render_to_response('challenges/challenge.html', context,
                              context_instance=RequestContext(request))


def show_challenge_full(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)

    context = {
        'challenge': challenge,
    }

    return render_to_response('challenges/challenge_full.html', context,
                              context_instance=RequestContext(request))


@login_required
def create_submission(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)
    if not challenge.is_active():
        return HttpResponseForbidden(_("Challenge is not active"))

    user = request.user.get_profile()

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['title'] = truncatewords(post_data['summary'], 10)
        form = SubmissionForm(post_data)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.title = truncatewords(submission.summary, 10)
            submission.created_by = user
            submission.save()

            submission.challenge.add(challenge)

            messages.success(request, _('Your submission has been created'))

            return HttpResponseRedirect(reverse('submission_edit', kwargs={
                'slug': challenge.slug,
                'submission_id': submission.pk,
                }))
        else:
            messages.error(request, _('Unable to create your submission'))
    else:
        form = SubmissionForm()

    context = {
        'form': form,
        'challenge': challenge,
    }

    return render_to_response('challenges/submission_edit.html', context,
                              context_instance=RequestContext(request))


@login_required
@submission_owner_required
def edit_submission(request, slug, submission_id):
    challenge = get_object_or_404(Challenge, slug=slug)
    submission = get_object_or_404(Submission, pk=submission_id)

    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your submission has been edited.'))

            return HttpResponseRedirect(reverse('submission_show', kwargs={
                'slug': challenge.slug,
                'submission_id': submission.pk,
            }))
        else:
            messages.error(request, _('Unable to update your submission'))
    else:
        form = SubmissionForm(instance=submission)

    ctx = {
        'challenge': challenge,
        'submission': submission,
        'form': form,
    }

    return render_to_response('challenges/submission_edit_summary.html',
                              ctx, context_instance=RequestContext(request))


@login_required
@submission_owner_required
def edit_submission_description(request, slug, submission_id):
    challenge = get_object_or_404(Challenge, slug=slug)
    submission = get_object_or_404(Submission, pk=submission_id)

    if request.method == 'POST':
        form = SubmissionDescriptionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your submission has been edited.'))

            return HttpResponseRedirect(reverse('submission_show', kwargs={
                'slug': challenge.slug,
                'submission_id': submission.pk
            }))
        else:
            messages.error(request, _('Unable to update your submission'))
    else:
        form = SubmissionDescriptionForm(instance=submission)

    ctx = {
        'challenge': challenge,
        'submission': submission,
        'form': form
    }

    return render_to_response('challenges/submission_edit_description.html',
                              ctx, context_instance=RequestContext(request))


@login_required
@submission_owner_required
def edit_submission_share(request, slug, submission_id):
    challenge = get_object_or_404(Challenge, slug=slug)
    submission = get_object_or_404(Submission, pk=submission_id)

    url = request.build_absolute_uri(reverse('submission_show', kwargs={
        'slug': challenge.slug, 'submission_id': submission.pk
    }))

    ctx = {
        'challenge': challenge,
        'submission': submission,
        'url': url,
    }

    return render_to_response('challenges/submission_edit_share.html',
                              ctx, context_instance=RequestContext(request))


def show_submission(request, slug, submission_id):
    challenge = get_object_or_404(Challenge, slug=slug)
    submission = get_object_or_404(Submission, pk=submission_id)

    context = {
        'challenge': challenge,
        'submission': submission,
    }

    return render_to_response('challenges/submission_show.html', context,
                              context_instance=RequestContext(request))


@login_required
@challenge_owner_required
def challenge_judges(request, slug):
    challenge = get_object_or_404(Challenge, slug=slug)

    if request.method == 'POST':
        form = JudgeForm(request.POST)
        if form.is_valid():
            judge = form.save(commit=False)
            judge.challenge = challenge

            try:
                judge.save()
                messages.success(request, _('Judge has been added'))
            except IntegrityError:
                messages.error(request, _('User is already a judge'))

            return HttpResponseRedirect(reverse('challenges_judges', kwargs={
                'slug': challenge.slug,
            }))
        else:
            messages.error(request, _('Unable to add judge.'))
    else:
        form = JudgeForm()

    judges = Judge.objects.filter(challenge=challenge)

    context = {
        'challenge': challenge,
        'form': form,
        'judges': judges,
    }

    return render_to_response('challenges/challenge_judges.html', context,
                              context_instance=RequestContext(request))


@login_required
@challenge_owner_required
def challenge_judges_delete(request, slug, judge):
    if request.method == 'POST':
        challenge = get_object_or_404(Challenge, slug=slug)
        judge = get_object_or_404(Judge, pk=judge)
        if judge.challenge != challenge:
            return HttpResponseForbidden(_("You are not judge of this challenge"))
        judge.delete()
        messages.success(request, _('Judge removed.'))
    return HttpResponseRedirect(reverse('challenges_judges', kwargs={
        'slug': challenge.slug,
    }))


@login_required
def submissions_voter_details(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)

    try:
        voter = VoterDetails.objects.get(user=request.user.get_profile())
    except:
        voter = None

    if request.method == 'POST':
        form = VoterDetailsForm(request.POST, instance=voter)
        if form.is_valid():
            details = form.save(commit=False)
            details.user = request.user.get_profile()
            details.save()
            form.save_m2m()

            messages.success(request, _('Your details were saved.'))

            return HttpResponseRedirect(reverse('challenges_show', kwargs={
                'slug': submission.challenge.get().slug,
            }))
        else:
            messages.error(request, _('Unable to save details'))
    else:
        form = VoterDetailsForm(instance=voter)
    context = {
        'form': form,
        'submission': submission,
    }

    return render_to_response('challenges/voter_details.html', context,
                              context_instance=RequestContext(request))
