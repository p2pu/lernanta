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
from django.db.models import Q, Count, Max
from django.contrib.contenttypes.models import ContentType

# from links.tasks import UnsubscribeFromFeed
from pagination.views import get_pagination_context

from projects.models import Project
from learn import forms as project_forms
from learn.models import get_listed_courses
from learn.models import get_popular_tags
from learn.models import get_weighted_tags
from learn.models import get_courses_by_tag
from learn.models import get_courses_by_tags
from learn.models import get_courses_by_list
from learn.models import get_tags_for_courses
from l10n.urlresolvers import reverse
from relationships.models import Relationship
from schools.models import School
from activity.models import Activity, RemoteObject
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


def learn(request, max_count=24):
    projects = get_listed_courses().order_by('-created_on')
    get_params = request.GET.copy()
    if not 'language' in get_params:
        language = request.session.get('search_language') or 'all'
        get_params['language'] = language
    form = project_forms.ProjectsFilterForm(get_params)
 
    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'learn_url': reverse('learn_all'),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
    }
    if form.is_valid():
        language = form.cleaned_data['language']
        request.session['search_language'] = language
        if language != 'all':
            projects = projects.filter(language__startswith=language)

        reviewed = form.cleaned_data['reviewed']
        if reviewed:
            accepted_reviews = Review.objects.filter(
                accepted=True).values('project_id')
            projects = projects.filter(id__in=accepted_reviews)

    return _filter_and_return(request, context, projects, max_count)


def schools(request, school_slug, max_count=24):
    school = get_object_or_404(School, slug=school_slug)
    projects = get_listed_courses().order_by('-created_on')

    get_params = request.GET.copy()
    if not 'language' in get_params:
        language = request.session.get('search_language') or 'all'
        get_params['language'] = language
    form = project_forms.ProjectsFilterForm(get_params)

    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'learn_url': reverse('learn_all'),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
        'learn_school': school,
    }

    projects = projects.filter(school=school)

    if form.is_valid():
        language = form.cleaned_data['language']
        request.session['search_language'] = language
        if language != 'all':
            projects = projects.filter(language__startswith=language)
    
    return _filter_and_return(request, context, projects, max_count)

   
def featured(request, feature, max_count=24):
    projects = get_listed_courses().order_by('-created_on')
    get_params = request.GET.copy()

    if not 'language' in get_params:
        language = request.session.get('search_language') or 'all'
        get_params['language'] = language

    form = project_forms.ProjectsFilterForm(get_params)

    context = {
        'schools': School.objects.all(),
        'popular_tags': get_popular_tags(),
        'form': form,
        'learn_url': reverse('learn_all'),
        'infinite_scroll': request.GET.get('infinite_scroll', False),
    }

    projects = get_courses_by_list(feature, projects)
    context['learn_{0}'.format(feature)] = True

    if form.is_valid():
        language = form.cleaned_data['language']
        request.session['search_language'] = language
        if language != 'all':
            projects = projects.filter(language__startswith=language)
    
    return _filter_and_return(request, context, projects, max_count)

    
def learn_tags(request):
    tags = get_weighted_tags()
    return render_to_response('learn/learn_tags.html', {'tags': tags},
        context_instance=RequestContext(request))

