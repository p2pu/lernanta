import logging
import datetime
import unicodecsv
import itertools

from django import http
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string

from pagination.views import get_pagination_context

from learn.forms import CourseFilterForm
from learn.models import get_listed_courses
from learn.models import get_popular_tags
from learn.models import get_weighted_tags
from learn.models import get_courses_by_tags
from learn.models import get_courses_by_list
from learn.models import get_courses_by_language
from learn.models import get_tags_for_courses
from learn.models import search_course_title
from l10n.urlresolvers import reverse
from schools.models import School
from reviews.models import Review

log = logging.getLogger(__name__)


def _filter_and_return(request, context, projects, max_count):
    tag_string = request.GET.get('filter_tags')
    filter_tags = []
    if tag_string:
        filter_tags = tag_string.split('|')
    context['filter_tags'] = filter_tags
    
    if filter_tags:
        projects = get_courses_by_tags(filter_tags, projects)

    language = request.session.get('search_language', 'all')
    projects = get_courses_by_language(language, projects)

    context['popular_tags'] = get_tags_for_courses(projects, filter_tags)
    context['projects'] = projects
    context.update(get_pagination_context(request, projects, max_count))
    if request.is_ajax():
        projects_html = render_to_string('learn/_learn_projects.html',
            context, context_instance=RequestContext(request))
        projects_pagination = render_to_string('learn/_learn_pagination.html',
            context, context_instance=RequestContext(request))
        learn_header = render_to_string('learn/_learn_header.html',
            context, context_instance=RequestContext(request))
        learn_filters = render_to_string('learn/_learn_filters.html',
            context, context_instance=RequestContext(request))
        data = {
            'projects_html': projects_html,
            'projects_pagination': projects_pagination,
            'learn_header': learn_header,
            'learn_filters': learn_filters,
        }
        json = simplejson.dumps(data)
        return http.HttpResponse(json, mimetype="application/json")
    return render_to_response('learn/learn.html', context,
        context_instance=RequestContext(request))


def _language_prefs(request):
    get_params = request.GET.copy()
    if not 'language' in get_params:
        language = request.session.get('search_language') or 'all'
        get_params['language'] = language
    form = CourseFilterForm(get_params)

    if form.is_valid():
        language = form.cleaned_data['language']
        request.session['search_language'] = language

    return form


def learn(request, max_count=24):
    projects = get_courses_by_list('listed')
    
    form = _language_prefs(request)

    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'load_more_url': reverse('learn_all'),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
    }

    return _filter_and_return(request, context, projects, max_count)


def schools(request, school_slug, max_count=24):
    school = get_object_or_404(School, slug=school_slug)
    projects = get_listed_courses()

    form = _language_prefs(request)
     
    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'load_more_url': reverse('learn_schools', kwargs={"school_slug": school_slug}),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
        'learn_school': school,
    }

    #projects = projects.filter(school=school)
    projects = get_courses_by_list(school_slug, projects)
  
    return _filter_and_return(request, context, projects, max_count)


def fresh(request, max_count=24):
    context = {
        "learn_fresh": True,
        'schools': School.objects.all()
    }
    projects = get_listed_courses()[:24]
    return _filter_and_return(request, context, projects, max_count)

   
def list(request, list_name, max_count=24):
    projects = get_listed_courses()
    get_params = request.GET.copy()

    form = _language_prefs(request)
 
    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'load_more_url': reverse('learn_list', kwargs={"list_name": list_name}),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
    }

    projects = get_courses_by_list(list_name, projects)
    context['learn_{0}'.format(list_name)] = True

    return _filter_and_return(request, context, projects, max_count)

    
def learn_tags(request):
    tags = get_weighted_tags()
    return render_to_response('learn/learn_tags.html', {'tags': tags},
        context_instance=RequestContext(request))


def auto_complete_lookup(request):
    term = request.GET.get('term', None)
    course_list = []

    if term:
        course_list = search_course_title(term)

    json = simplejson.dumps(
        [{"label": u"{0} ({1})".format(course.title, course.url), "url": course.url} for course in course_list]
    )
    return http.HttpResponse(json, mimetype="application/json")


def add_course(request):
    return render_to_response('learn/add_course.html', {}, 
        context_instance=RequestContext(request))


def update_course(request):
    pass
