import logging

from django import http
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.utils import simplejson as json
from django.views.decorators.http import require_http_methods

from l10n.urlresolvers import reverse
from users.decorators import login_required
from drumbeat import messages

from courses import models as course_model
from courses.forms import CourseCreationForm
from courses.forms import CourseUpdateForm
from courses.forms import CourseTermForm
from courses.forms import CourseImageForm
from courses.forms import CohortSignupForm
from courses.forms import CourseTagsForm
from courses.decorators import require_organizer

from content2 import models as content_model
from content2.forms import ContentForm
from content2 import utils

from media import models as media_model

from replies import models as comment_model

log = logging.getLogger(__name__)


def _get_course_or_404( course_uri ):
    try:
        course = course_model.get_course(course_uri)
    except:
        raise http.Http404
    return course


def _populate_course_context( request, course_id, context ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
    context['course'] = course
    context['course_url'] = request.get_full_path()
    if 'image_uri' in course:
        context['course']['image'] = media_model.get_image(course['image_uri'])

    #NOTE if performance becomes a problem dont fetch cohort
    cohort = course_model.get_course_cohort(course_uri)
    context['cohort'] = cohort
    user_uri = "/uri/user/{0}".format(request.user.username)
    context['organizer'] = course_model.is_cohort_organizer(
        user_uri, cohort['uri']
    )
    context['organizer'] |= request.user.is_superuser
    if course_model.user_in_cohort(user_uri, cohort['uri']):
        if not context['organizer']:
            context['show_leave_course'] = True
        context['learner'] = True
    elif cohort['signup'] == "OPEN":
        context['show_signup'] = True

    return context

@login_required
def create_course( request ):
    if request.method == "POST":
        form = CourseCreationForm(request.POST)
        if form.is_valid():
            user = request.user.get_profile()
            user_uri = "/uri/user/{0}".format(user.username)
            course = {
                'title': form.cleaned_data.get('title'),
                'hashtag': form.cleaned_data.get('hashtag'),
                'description': form.cleaned_data.get('description'),
                'language': form.cleaned_data.get('language'),
                'organizer_uri': user_uri
            }
            course = course_model.create_course(**course)
            redirect_url = reverse('courses_show', 
                kwargs={'course_id': course['id'], 'slug': course['slug']}
            )
            return http.HttpResponseRedirect(redirect_url)
    else:
        form = CourseCreationForm(initial={'language': get_language()})

    context = { 'form': form }
    return render_to_response('courses/create_course.html', 
        context, context_instance=RequestContext(request)
    )


def import_project( request, project_slug ):
    from projects.models import Project
    project = get_object_or_404(Project, slug=project_slug)
    from courses import utils
    course = utils.import_project(project, project.name[:3])
    cohort = course_model.get_course_cohort(course['uri'])
    user_uri = "/uri/user/{0}".format(request.user.username)
    course_model.add_user_to_cohort(cohort['uri'], user_uri, "ORGANIZER")
    return course_slug_redirect(request, course['id'])


def course_slug_redirect( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
    redirect_url = reverse('courses_show', 
        kwargs={'course_id': course_id, 'slug': course['slug']})
    return http.HttpResponseRedirect(redirect_url)


def show_course( request, course_id, slug=None ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
    
    if slug != course['slug']:
        return course_slug_redirect( request, course_id)

    context = { }
    context = _populate_course_context(request, course_id, context)
    context['about_active'] = True

    if context['organizer']:
        context['update_form'] = CourseUpdateForm(course)

    context['about'] = content_model.get_content(course['about_uri'])

    return render_to_response(
        'courses/course.html',
        context,
        context_instance=RequestContext(request)
    )


def course_learn_api_data( request, course_id ):
    """ return data required by the learn API """
    course_uri = course_model.course_id2uri(course_id)
    try:
        course_data = course_model.get_course_learn_api_data(course_uri)
    except:
        raise http.Http404

    return http.HttpResponse(json.dumps(course_data), mimetype="application/json")
 

@login_required
@require_organizer
def course_admin_content( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
 
    context = { }
    context = _populate_course_context(request, course_id, context)
    context['content_active'] = True

    return render_to_response(
        'courses/course_admin_content.html',
        context,
        context_instance=RequestContext(request)
    )


def course_discussion( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
 
    context = { }
    context = _populate_course_context(request, course_id, context)
    context['discussion_active'] = True

    return render_to_response(
        'courses/course_discussion.html',
        context,
        context_instance=RequestContext(request)
    )


def course_people( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
 
    context = { }
    context = _populate_course_context(request, course_id, context)

    from users.models import get_user_profile_image_url
    for user in context['cohort']['users'].values():
        user['profile_image_url'] = get_user_profile_image_url(user['uri'])

    context['people_active'] = True

    return render_to_response(
        'courses/course_people.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
@require_organizer
def course_settings( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
 
    context = { }
    context = _populate_course_context(request, course_id, context)

    context['update_form'] = CourseUpdateForm(course)
    context['image_form'] = CourseImageForm()
    tags = ", ".join(course_model.get_course_tags(course_uri))
    context['tags_form'] = CourseTagsForm({'tags': tags})
    if context['cohort']['term'] == 'FIXED':
        context['term_form'] = CourseTermForm(context['cohort'])
    else:
        context['term_form'] = CourseTermForm()
    context['signup_form'] = CohortSignupForm(
        initial={'signup': context['cohort']['signup']}
    )
    context['settings_active'] = True

    return render_to_response(
        'courses/course_settings.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_image( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    user_uri = "/uri/user/{0}".format(request.user.username)
    image_form = CourseImageForm(request.POST, request.FILES)
    if image_form.is_valid():
        image_file = request.FILES['image']
        image = media_model.upload_image(image_file, course_uri)
        course_model.update_course(
            course_uri=course_uri,
            image_uri=image['uri'],
        )
    else:
        messages.error(request, _("Could not upload image"))
    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
def course_signup( request, course_id ):
    #NOTE: consider using cohort_id in URL to avoid cohort lookup
    cohort = course_model.get_course_cohort( course_id )
    user_uri = "/uri/user/{0}".format(request.user.username)
    if cohort['signup'] == "OPEN":
        course_model.add_user_to_cohort(cohort['uri'], user_uri, "LEARNER", True)
        messages.success(request, _("You are now signed up for this course."))
    else:
        messages.error(request, _("This course isn't open for signup."))
    return course_slug_redirect( request, course_id )


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_add_user( request, course_id ):
    cohort_uri = course_model.get_course_cohort_uri(course_id)
    redirect_url = reverse('courses_people', kwargs={'course_id': course_id})
    username = request.POST.get('username', None)

    if not username:
        messages.error(request, _("Please select a user to add."))
        return http.HttpResponseRedirect(redirect_url)

    user_uri = "/uri/user/{0}".format(username)
    try:
        course_model.add_user_to_cohort(cohort_uri, user_uri, "LEARNER")
        messages.success(request, _("User added."))
    except course_model.ResourceNotFoundException as e:
        messages.error(request, _("User does not exist."))

    return http.HttpResponseRedirect(redirect_url)


@login_required
def course_leave( request, course_id, username ):
    cohort_uri = course_model.get_course_cohort_uri(course_id)
    user_uri = "/uri/user/{0}".format(request.user.username)
    is_organizer = course_model.is_cohort_organizer(
        user_uri, cohort_uri
    )
    removed = False
    error_message = _("Could not remove user")
    if username == request.user.username or is_organizer:
        removed, error_message = course_model.remove_user_from_cohort(
            cohort_uri, "/uri/user/{0}".format(username)
        )

    if not removed:
        messages.error(request, error_message)

    if is_organizer:
        redirect_url = reverse('courses_people', kwargs={'course_id': course_id})
        return http.HttpResponseRedirect(redirect_url)

    return course_slug_redirect( request, course_id)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_add_organizer( request, course_id, username ):
    cohort_uri = course_model.get_course_cohort_uri(course_id)
    user_uri = "/uri/user/{0}".format(request.user.username)
    is_organizer = course_model.is_cohort_organizer(
        user_uri, cohort_uri
    )
    if not is_organizer and not request.user.is_superuser:
        messages.error( request, _("Only other organizers can add a new organizer") )
        return course_slug_redirect( request, course_id)
    new_organizer_uri = "/uri/user/{0}".format(username)
    course_model.remove_user_from_cohort(cohort_uri, new_organizer_uri)
    course_model.add_user_to_cohort(cohort_uri, new_organizer_uri, "ORGANIZER")

    #TODO
    redirect_url = reverse('courses_people', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_change_status( request, course_id, status ):
    user_uri = "/uri/user/{0}".format(request.user.username)
    course_uri = course_model.course_id2uri(course_id)
    if status == 'draft':
        course = course_model.unpublish_course(course_uri)
    elif status == 'publish':
        course = course_model.publish_course(course_uri)
    elif status == 'archive':
        course = course_model.archive_course(course_uri)
    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_change_signup( request, course_id ):
    form = CohortSignupForm(request.POST)
    if form.is_valid():
        signup = form.cleaned_data['signup']
        cohort_uri = course_model.get_course_cohort_uri(course_id)
        cohort = course_model.update_cohort(cohort_uri, signup=signup.upper())
        if not cohort:
            messages.error( request, _("Could not change cohort signup"))
    else:
        request.messages.error(request, _("Invalid choice for signup"))
    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_change_term( request, course_id, term ):
    cohort_uri = course_model.get_course_cohort_uri( course_id )
    if term == 'fixed':
        form = CourseTermForm(request.POST)
        if form.is_valid():
            course_model.update_cohort(
                cohort_uri,
                term=term.upper(),
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date']
            )
        else:
            messages.error( request, _("Could not update fixed term dates"))
    elif term == 'rolling':
        course_model.update_cohort(cohort_uri, term=term.upper())
    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_update_attribute( request, course_id, attribute):
    course_uri = course_model.course_id2uri(course_id)
    form = CourseUpdateForm(request.POST)
    if form.is_valid():
        kwargs = { attribute: form.cleaned_data[attribute] }
        course_model.update_course( course_uri, **kwargs )
    else:
        messages.error(request, _("Could not update {0}.".format(attribute)))
    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
@require_organizer
def course_update_tags( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    form = CourseTagsForm(request.POST)
    if form.is_valid():
        tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
        course_model.remove_course_tags(
            course_uri, course_model.get_course_tags(course_uri)
        )
        course_model.add_course_tags(course_uri, tags)
        messages.success( request, _("Course tags successfully updated") )

    redirect_url = reverse('courses_settings', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


def show_content( request, course_id, content_id):
    content_uri = '/uri/content/{0}'.format(content_id)
    user_uri = "/uri/user/{0}".format(request.user.username)
    content = content_model.get_content(content_uri)
    context = { 
        'content': content, 
    }
    context = _populate_course_context(request, course_id, context)
    context['content_active'] = True
    #context['comments'] = course_model.get_cohort_comments(cohort['uri'], content['uri'])
    context['can_edit'] = context['organizer']
    context['form'] = ContentForm(content)
    return render_to_response(
        'courses/content.html', 
        context, 
        context_instance=RequestContext(request)
    )


@login_required
@require_organizer
def create_content( request, course_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
    if request.method == "POST":
        form = ContentForm(request.POST)
        if form.is_valid():
            user = request.user.get_profile()
            user_uri = "/uri/user/{0}".format(user.username)
            content_data = {
                'title': form.cleaned_data.get('title'),
                'content': form.cleaned_data.get('content'),
                'author_uri': user_uri,
            }
            content = content_model.create_content(**content_data)
            course_model.add_course_content(course['uri'], content['uri'])

            redirect_url = request.POST.get('next_url', None)
            if not redirect_url:
                redirect_url = reverse('courses_show',
                    kwargs={'course_id': course['id'], 'slug': course['slug']}
                )
            return http.HttpResponseRedirect(redirect_url)
    else:
        form = ContentForm()

    context = { 'form': form }
    context = _populate_course_context(request, course_id, context)
    if request.GET.get('next_url', None):
        context['next_url'] = request.GET.get('next_url', None)

    return render_to_response('courses/create_content.html', 
        context, context_instance=RequestContext(request)
    )


@login_required
@require_organizer
def edit_content( request, course_id, content_id ):
    course_uri = course_model.course_id2uri(course_id)
    course = _get_course_or_404(course_uri)
    content = content_model.get_content("/uri/content/{0}".format(content_id))

    if request.method == "POST":
        form = ContentForm(request.POST)
        if form.is_valid():
            content_data = {
                'title': form.cleaned_data.get('title'),
                'content': form.cleaned_data.get('content'),
            }
            user = request.user.get_profile()
            user_uri = "/uri/user/{0}".format(user.username)
            content = content_model.update_content(
                content['uri'], content_data['title'], 
                content_data['content'], user_uri
            )
            
            redirect_url = request.POST.get('next_url', None)
            if not redirect_url:
                redirect_url = reverse('courses_content_show',
                    kwargs={'course_id': course_id, 'content_id': content_id}
                )
            return http.HttpResponseRedirect(redirect_url)
    else:
        form = ContentForm(initial=content)

    context = {
        'form': form,
        'content': content,
    }
    context = _populate_course_context(request, course_id, context)
    if request.GET.get('next_url', None):
        context['next_url'] = request.GET.get('next_url', None)
    return render_to_response('courses/edit_content.html', 
        context, context_instance=RequestContext(request)
    )


@login_required
@require_http_methods(['POST'])
def preview_content( request ):
    content = request.POST.get('content')
    from content2 import utils
    content = utils.clean_user_content(content)
    content = render_to_string("courses/preview_content_snip.html", 
        {'content':content })
    return http.HttpResponse(content, mimetype="application/json")


@login_required
@require_organizer
def remove_content( request, course_id, content_id ):
    course_uri = course_model.course_id2uri(course_id)
    content_uri = "/uri/content/{0}".format(content_id)
    course_model.remove_course_content(course_uri, content_uri)
    redirect_url = reverse('courses_admin_content', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_organizer
def move_content_up( request, course_id, content_id ):
    result = course_model.reorder_course_content(
        "/uri/content/{0}".format(content_id), "UP"
    )
    if not result:
        messages.error(request, _("Could not move content up!"))
    redirect_url = reverse('courses_admin_content', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_organizer
def move_content_down( request, course_id, content_id ):
    result = course_model.reorder_course_content(
        "/uri/content/{0}".format(content_id), "DOWN"
    )
    if not result:
        messages.error(request, _("Could not move content down!"))
    redirect_url = reverse('courses_admin_content', kwargs={'course_id': course_id})
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
def post_content_comment( request, course_id, content_id):
    #TODO use form with field that sanitizes the input!
    comment_content = request.POST.get('comment')
    user = request.user.get_profile()
    user_uri = "/uri/user/{0}".format(user.username)
    comment = comment_model.create_comment(comment_content, user_uri)

    reference_uri = "/uri/content/{0}".format(content_id)
    course_uri = course_model.course_id2uri(course_id)
    cohort = course_model.get_course_cohort(course_uri)
    course_model.add_comment_to_cohort(
        comment['uri'], cohort['uri'], reference_uri
    )

    if request.POST.get('next_url'):
        redirect_url = request.POST.get('next_url')
    else:
        redirect_url = reverse('courses_content_show',
            kwargs={'course_id': course_id, 'content_id': content_id}
        )
    return http.HttpResponseRedirect(redirect_url)


@login_required
@require_http_methods(['POST'])
def post_comment_reply( request, course_id, content_id, comment_id):
    #TODO use form with field that sanitizes the input!
    comment_content = request.POST.get('comment')
    user = request.user.get_profile()
    user_uri = "/uri/user/{0}".format(user.username)
    comment_uri = "/uri/comment/{0}".format(comment_id)
    reply = comment_model.reply_to_comment(
        comment_uri, comment_content, user_uri
    )

    #TODO: need to set reference so that lookup from comment works!

    if request.POST.get('next_url'):
        redirect_url = request.POST.get('next_url')
    else:
        redirect_url = reverse('courses_content_show',
            kwargs={'course_id': course_id, 'content_id': content_id}
        )
    return http.HttpResponseRedirect(redirect_url)
