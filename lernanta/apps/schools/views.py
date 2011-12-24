from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django import http
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType

from commonware.decorators import xframe_sameorigin

from users.decorators import login_required
from drumbeat import messages
from projects.models import Project, Participation
from users.models import UserProfile
from l10n.urlresolvers import reverse
from content.models import Page
from replies.models import PageComment
from statuses.models import Status
from activity.models import Activity
from activity.schema import verbs
from relationships.models import Relationship
from signups.models import SignupAnswer

from schools.decorators import school_organizer_required
from schools.models import School, ProjectSet
from schools import forms as school_forms


def home(request, slug):
    school = get_object_or_404(School, slug=slug)
    user = request.user
    if user.is_authenticated():
        profile = user.get_profile()
        is_organizer = school.organizers.filter(id=profile.id).exists()
    else:
        is_organizer = False
    context = {
        'school': school,
        'is_organizer': is_organizer,
    }
    return render_to_response('schools/home.html', context,
        context_instance=RequestContext(request))

def projectset(request, slug, set_slug):
    projectset = get_object_or_404(ProjectSet, slug=set_slug,
        school__slug=slug)
    return render_to_response('schools/projectset_home.html',
        {'projectset': projectset, 'school': projectset.school},
        context_instance=RequestContext(request))

def school_css(request, slug):
    school = get_object_or_404(School, slug=slug)
    return render_to_response('schools/school.css', {'school': school},
        context_instance=RequestContext(request), mimetype='text/css')


def multiple_school_css(request):
    schools = School.objects.all()
    return render_to_response('schools/multiple_school.css',
        {'schools': schools}, context_instance=RequestContext(request),
        mimetype='text/css')


@login_required
@school_organizer_required
def edit(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, _('School updated!'))
            return http.HttpResponseRedirect(
                reverse('schools_edit', kwargs=dict(slug=school.slug)))
    else:
        form = school_forms.SchoolForm(instance=school)

    return render_to_response('schools/school_edit_summary.html', {
        'form': form,
        'school': school,
        'summary_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def edit_styles(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolStylesForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, _('School styles updated!'))
            return http.HttpResponseRedirect(
                reverse('schools_edit_styles', kwargs=dict(slug=school.slug)))
    else:
        form = school_forms.SchoolStylesForm(instance=school)

    return render_to_response('schools/school_edit_styles.html', {
        'form': form,
        'school': school,
        'styles_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@xframe_sameorigin
@school_organizer_required
@require_http_methods(['POST'])
def edit_logo_async(request, slug):
    school = get_object_or_404(School, slug=slug)
    form = school_forms.SchoolLogoForm(request.POST, request.FILES,
                                          instance=school)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.logo.name,
        }))
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@login_required
@school_organizer_required
def edit_logo(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolLogoForm(request.POST, request.FILES,
                                              instance=school)
        if form.is_valid():
            messages.success(request, _('Image updated'))
            form.save()
            return http.HttpResponseRedirect(reverse('school_edit_logo',
                kwargs={'slug': school.slug}))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = school_forms.SchoolLogoForm(instance=school)
    return render_to_response('schools/school_edit_logo.html', {
        'school': school,
        'form': form,
        'logo_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@xframe_sameorigin
@school_organizer_required
@require_http_methods(['POST'])
def edit_groups_icon_async(request, slug):
    school = get_object_or_404(School, slug=slug)
    form = school_forms.SchoolGroupsIconForm(request.POST, request.FILES,
                                          instance=school)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.groups_icon.name,
        }))
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@login_required
@school_organizer_required
def edit_groups_icon(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolGroupsIconForm(request.POST, request.FILES,
                                              instance=school)
        if form.is_valid():
            messages.success(request, _('Image updated'))
            form.save()
            return http.HttpResponseRedirect(reverse('school_edit_groups_icon',
                kwargs={'slug': school.slug}))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = school_forms.SchoolGroupsIconForm(instance=school)
    return render_to_response('schools/school_edit_groups_icon.html', {
        'school': school,
        'form': form,
        'groups_icon_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@xframe_sameorigin
@school_organizer_required
@require_http_methods(['POST'])
def edit_background_async(request, slug):
    school = get_object_or_404(School, slug=slug)
    form = school_forms.SchoolBackgroundForm(request.POST, request.FILES,
                                          instance=school)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.background.name,
        }))
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@login_required
@school_organizer_required
def edit_background(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolBackgroundForm(request.POST, request.FILES,
                                              instance=school)
        if form.is_valid():
            messages.success(request, _('Image updated'))
            form.save()
            return http.HttpResponseRedirect(reverse('school_edit_background',
                kwargs={'slug': school.slug}))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = school_forms.SchoolBackgroundForm(instance=school)
    return render_to_response('schools/school_edit_background.html', {
        'school': school,
        'form': form,
        'background_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@xframe_sameorigin
@school_organizer_required
@require_http_methods(['POST'])
def edit_site_logo_async(request, slug):
    school = get_object_or_404(School, slug=slug)
    form = school_forms.SchoolSiteLogoForm(request.POST, request.FILES,
                                          instance=school)
    if form.is_valid():
        instance = form.save()
        return http.HttpResponse(simplejson.dumps({
            'filename': instance.site_logo.name,
        }))
    return http.HttpResponse(simplejson.dumps({
        'error': 'There was an error uploading your image.',
    }))


@login_required
@school_organizer_required
def edit_site_logo(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolSiteLogoForm(request.POST, request.FILES,
                                              instance=school)
        if form.is_valid():
            messages.success(request, _('Image updated'))
            form.save()
            return http.HttpResponseRedirect(reverse('school_edit_site_logo',
                kwargs={'slug': school.slug}))
        else:
            messages.error(request,
                           _('There was an error uploading your image'))
    else:
        form = school_forms.SchoolSiteLogoForm(instance=school)
    return render_to_response('schools/school_edit_site_logo.html', {
        'school': school,
        'form': form,
        'site_logo_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def edit_organizers(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.ProjectAddOrganizerForm(school, request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            school.organizers.add(user)
            school.save()
            messages.success(request, _('School organizer added.'))
            return http.HttpResponseRedirect(reverse(
                'schools_edit_organizers', kwargs=dict(slug=school.slug)))
        else:
            messages.error(request,
                _('There was an error adding the school organizer.'))
    else:
        form = school_forms.ProjectAddOrganizerForm(school)
    return render_to_response('schools/school_edit_organizers.html', {
        'school': school,
        'form': form,
        'organizers_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def matching_non_organizers(request, slug):
    school = get_object_or_404(School, slug=slug)
    if len(request.GET['term']) == 0:
        raise http.Http404

    non_organizers = UserProfile.objects.filter(deleted=False).exclude(
        id__in=school.organizers.values('user_id'))
    matching_users = non_organizers.filter(
        username__icontains=request.GET['term'])
    json = simplejson.dumps([user.username for user in matching_users])

    return http.HttpResponse(json, mimetype="application/json")


@login_required
@school_organizer_required
def edit_featured(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolAddFeaturedForm(school, request.POST)
        if form.is_valid():
            project = form.cleaned_data['project']
            school.featured.add(project)
            school.save()
            msg = _('The %s is now featured for this school.')
            messages.success(request, msg % project.kind.lower())
            return http.HttpResponseRedirect(reverse(
                'schools_edit_featured', kwargs=dict(slug=school.slug)))
        else:
            msg = _("There was an error marking %s as featured.")
            messages.error(request, msg % slug)
    else:
        form = school_forms.SchoolAddFeaturedForm(school)
    return render_to_response('schools/school_edit_featured.html', {
        'school': school,
        'form': form,
        'featured': school.featured.all(),
        'featured_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def matching_non_featured(request, slug):
    school = get_object_or_404(School, slug=slug)
    if len(request.GET['term']) == 0:
        raise http.Http404

    school_projects = Project.objects.filter(school=school)
    non_featured = school_projects.exclude(id__in=school.featured.values('id'))
    matching_projects = non_featured.filter(
        slug__icontains=request.GET['term'])
    json = simplejson.dumps([project.slug for project in matching_projects])

    return http.HttpResponse(json, mimetype="application/json")


@login_required
@school_organizer_required
def edit_featured_delete(request, slug, project_slug):
    school = get_object_or_404(School, slug=slug)
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == 'POST':
        school.featured.remove(project)
        msg = _("The %s stopped being featured for this school.")
        messages.success(request, msg % project.kind.lower())
    return http.HttpResponseRedirect(reverse('schools_edit_featured', kwargs={
        'slug': school.slug,
    }))


@login_required
@school_organizer_required
def edit_membership(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolAddProjectForm(school, request.POST)
        if form.is_valid():
            project = form.cleaned_data['project']
            project.school = school
            project.save()
            messages.success(request,
                _('The %s was added to this school.') % project.kind.lower())
            return http.HttpResponseRedirect(reverse('schools_edit_membership',
                kwargs=dict(slug=school.slug)))
        else:
            messages.error(request,
                _("There was an adding %s to this school.") % slug)
    else:
        form = school_forms.SchoolAddProjectForm(school)
    return render_to_response('schools/school_edit_membership.html', {
        'school': school,
        'form': form,
        'projects': school.projects.all(),
        'membership_tab': True,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def matching_non_member(request, slug):
    school = get_object_or_404(School, slug=slug)
    if len(request.GET['term']) == 0:
        raise http.Http404

    matching_projects = Project.objects.filter(
        slug__icontains=request.GET['term']).exclude(
        id__in=school.projects.all().values('id'))
    json = simplejson.dumps([project.slug for project in matching_projects])

    return http.HttpResponse(json, mimetype="application/json")


@login_required
@school_organizer_required
def edit_membership_delete(request, slug, project_slug):
    school = get_object_or_404(School, slug=slug)
    project = get_object_or_404(Project, slug=project_slug, school__slug=slug)
    if request.method == 'POST':
        project.school = None
        project.save()
        messages.success(request, _(
            "The %s is no longer part of this school.") % project.kind.lower())
    return http.HttpResponseRedirect(reverse('schools_edit_membership',
        kwargs={'slug': school.slug}))


@login_required
@school_organizer_required
def edit_statistics(request, slug):
    school = get_object_or_404(School, slug=slug)

    all_projects = school.projects.all()
    project_counts = {}
    for category, name in Project.CATEGORY_CHOICES:
        project_counts[category] = 0
    for project in all_projects:
        project_counts[project.category] += 1
    project_ct = ContentType.objects.get_for_model(Project)
    project_ids = school.projects.values('id')
    comments = PageComment.objects.filter(scope_content_type=project_ct,
        scope_id__in=project_ids)
    page_ct = ContentType.objects.get_for_model(Page)
    page_comments_count = comments.filter(page_content_type=page_ct).count()
    statuses_count = Status.objects.filter(project__in=project_ids).count()
    status_ct = ContentType.objects.get_for_model(Activity)
    activity_comments_count = comments.filter(
        page_content_type=status_ct).count()
    page_edits_count = Activity.objects.filter(scope_object__in=project_ids,
       target_content_type=page_ct, verb=verbs['update']).count()
    participations = Participation.objects.filter(project__in=project_ids)
    organizer_ids = participations.filter(organizing=True).values(
        'user__id')
    participant_ids = participations.filter(organizing=False).values(
        'user__id')
    follower_ids = Relationship.objects.filter(
        target_project__in=project_ids).exclude(
        source__in=organizer_ids).exclude(
        source__in=participant_ids).values('source_id').distinct()
    organizers_count = organizer_ids.distinct().count()
    participants_count = participant_ids.distinct().count()
    followers_count = follower_ids.distinct().count()
    signup_answers_count = SignupAnswer.objects.filter(
        sign_up__project__in=project_ids).count()
    signup_answer_ct = ContentType.objects.get_for_model(SignupAnswer)
    signup_comments_count = comments.filter(
        page_content_type=signup_answer_ct).count()

    return render_to_response('schools/school_edit_statistics.html', {
        'school': school,
        'statistics_tab': True,
        'project_counts': project_counts.items(),
        'page_comments_count': page_comments_count,
        'statuses_count': statuses_count,
        'activity_comments_count': activity_comments_count,
        'page_edits_count': page_edits_count,
        'organizers_count': organizers_count,
        'participants_count': participants_count,
        'followers_count': followers_count,
        'signup_answers_count': signup_answers_count,
        'signup_comments_count': signup_comments_count,
    }, context_instance=RequestContext(request))


@login_required
@school_organizer_required
def edit_mentorship(request, slug):
    school = get_object_or_404(School, slug=slug)
    if request.method == 'POST':
        form = school_forms.SchoolMentorshipForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, _('School mentorship details updated!'))
            return http.HttpResponseRedirect(
                reverse('schools_edit_mentorship',
                kwargs=dict(slug=school.slug)))
    else:
        form = school_forms.SchoolMentorshipForm(instance=school)

    return render_to_response('schools/school_edit_mentorship.html', {
        'form': form,
        'school': school,
        'mentorship_tab': True,
    }, context_instance=RequestContext(request))
