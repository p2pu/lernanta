from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q

from tags.models import GeneralTaggedItem
from projects.models import Project
from signups.models import Signup

import datetime

def get_active_languages():
    """ Return a list of the active language currently in use """
    language_list = Project.objects.all().values_list('language').distinct('language')
    language_dict = dict(settings.LANGUAGES)
    languages = [(l[0], language_dict[l[0]],) for l in language_list]
    return languages


def search(keyword, limit = 10):
    """ a simple 1 word search for courses, will match partial name
        or any tag.
    """
    results = []
    results += Project.objects.filter(name__icontains=keyword)[:limit]
    results += get_courses_by_tag(keyword)[:limit]
    return list(set(results))[:limit]


def get_listed_courses():
    """ return all the projects that should be listed """
    listed = Project.objects.filter(
        not_listed=False,
        deleted=False,
        archived=False,
        under_development=False,
        test=False)
    listed = listed.filter(Q(category=Project.CHALLENGE)
        | Q(sign_up__status=Signup.MODERATED)
        | Q(sign_up__status=Signup.NON_MODERATED))
    return listed


def get_popular_tags(max_count=10):
    """ return a list of popular tags """
    ct = ContentType.objects.get_for_model(Project)
    listed = list(get_listed_courses().values_list('id', flat=True))
    return GeneralTaggedItem.objects.filter(
        content_type=ct, object_id__in=listed).values(
        'tag__name').annotate(tagged_count=Count('object_id')).order_by(
        '-tagged_count')[:max_count]


def get_weighted_tags(min_count=2, min_weight=1.0, max_weight=7.0):
    ct = ContentType.objects.get_for_model(Project)
    listed = get_listed_courses().values('id')
    tags = GeneralTaggedItem.objects.filter(
        content_type=ct, object_id__in=listed).values(
        'tag__name').annotate(tagged_count=Count('object_id')).filter(
        tagged_count__gte=min_count)
    if tags.count():
        min_tagged_count = tags.order_by('tagged_count')[0]['tagged_count']
        max_tagged_count = tags.order_by('-tagged_count')[0]['tagged_count']
        if min_tagged_count == max_tagged_count:
            factor = 1.0
        else:
            factor = float(max_weight - min_weight) / float(max_tagged_count - min_tagged_count)
    tags = tags.order_by('tag__name')
    for tag in tags:
        tag['weight']  = max_weight - (max_tagged_count - tag['tagged_count']) * factor
    return tags


def get_tags_for_courses(courses, exclude=[], max_tags=6):
    ct = ContentType.objects.get_for_model(Project)
    course_ids = courses.values('id')
    tags = GeneralTaggedItem.objects.filter(
        content_type=ct, object_id__in=course_ids).values(
        'tag__name').exclude(tag__name__in=exclude).annotate(
        tagged_count=Count('object_id'))
    return tags.order_by('-tagged_count')[:max_tags]


def get_courses_by_tag(tag_name, projects=None):
    ct = ContentType.objects.get_for_model(Project)
    items = GeneralTaggedItem.objects.filter(
        content_type=ct, tag__name=tag_name).values(
        'object_id')
    if not projects:
        projects = Project.objects
    return projects.filter(id__in=items)


def get_courses_by_tags(tag_list, courses=None):
    "this will return courses that have all the tags in tag_list"
    if not courses:
        courses = Project.objects
    for tag in tag_list:
        courses = get_courses_by_tag(tag, courses)
    return courses


def get_courses_by_list(list_name, projects=None):
    """ return a list of projects
        if projects != None, only the courses in projects and the list
        will be returned.
    """
    if not projects:
        projects = Project.objects

    if list_name == 'showcase':
        projects = projects.filter(featured=True)
    elif list_name == 'community':
        projects = projects.filter(community_featured=True)
    elif list_name == 'fresh':
        one_week = datetime.datetime.now() - datetime.timedelta(weeks=1)
        projects = projects.filter(created_on__gte=one_week)
    elif list_name == 'popular':
        popular = Relationship.objects.filter(
            deleted=False, target_project__isnull=False).values(
            'target_project').annotate(Count('source')).order_by(
            '-source__count')[:max_count]
        popular_ids = [d['target_project'] for d in popular]
        projects = projects.filter(id__in=popular_ids)
    elif list_name == 'updated':
        external_ct = ContentType.objects.get_for_model(RemoteObject)
        relationship_ct = ContentType.objects.get_for_model(Relationship)
        last_updated = Activity.objects.filter(
            deleted=False, scope_object__isnull=False).exclude(
            target_content_type=external_ct).exclude(
            target_content_type=relationship_ct).values(
            'scope_object').annotate(Max('created_on')).order_by(
            '-created_on__max')[:max_count]
        last_updated_ids = [d['scope_object'] for d in last_updated]
        projects = projects.filter(id__in=last_updated_ids)

    return projects
