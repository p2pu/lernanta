import datetime

from django.conf import settings
from django.db.models import Count

from learn import db


def _get_listed_courses():
    listed = db.Course.objects.filter(
        date_removed__isnull=True
        #TODO ,verified=True
    )
    return listed


def get_listed_courses():
    """ return all the projects that should be listed """
    listed = _get_listed_courses().order_by("-date_added")
    #TODO convert to JSON?
    return listed


def get_active_languages():
    """ Return a list of the active language currently in use """
    language_list = _get_listed_courses().values_list('language').distinct('language')
    language_dict = dict(settings.LANGUAGES)
    languages = [(l[0], language_dict[l[0]],) for l in language_list]
    return languages


def get_courses_by_language(language, courses=None):
    if language == "all":
        return courses

    lang_courses = _get_listed_courses().order_by('-date_added').filter(language__startswith=language)
    if not courses == None:
        lang_courses = lang_courses.filter(url__in=[c.url for c in courses])
    return lang_courses


def get_popular_tags(max_count=10):
    """ return a list of popular tags """
    listed = _get_listed_courses()
    return db.CourseTags.objects.filter(course__in=listed).values(
        'tag').annotate(tagged_count=Count('course')).order_by(
        '-tagged_count')[:max_count]


def get_weighted_tags(min_count=2, min_weight=10, max_weight=26):
    listed = _get_listed_courses()
    tags = db.CourseTags.objects.filter(course__in=listed).values(
        'tag').annotate(count=Count('course'))
    minf = lambda x, y: x if x['count']<y['count'] else y
    maxf = lambda x, y: x if x['count']>y['count'] else y
    minv = reduce(minf, tags)['count']
    maxv = reduce(maxf, tags)['count']
    weighted_tags = [{'tag': tag['tag'], 'weight': min_weight+(max_weight-min_weight)*(tag['count']-minv)/(maxv - minv), 'count': tag['count']} for tag in tags]
    return weighted_tags


def get_tags_for_courses(courses, exclude=[], max_tags=6):
    tags = db.CourseTags.objects.filter(course__url__in=[c.url for c in courses])
    tags = tags.exclude(tag__in=exclude)
    tags = tags.values('tag')
    tags = tags.annotate(tagged_count=Count('course'))
    tags = tags.order_by('-tagged_count')[:max_tags]
    return tags


def get_courses_by_tag(tag_name, courses=None):
    if courses == None:
        courses=get_listed_courses()

    course_ids = db.CourseTags.objects.filter(
        tag=tag_name, 
        course__url__in=[c.url for c in courses]
    ).values_list('course', flat=True)
    ret = _get_listed_courses().order_by("-date_added").filter(id__in=course_ids)
    return ret


def get_courses_by_tags(tag_list, courses=None):
    "this will return courses that have all the tags in tag_list"
    if courses == None:
        courses = get_listed_courses()
    for tag in tag_list:
        courses = get_courses_by_tag(tag, courses)
    return courses


def get_courses_by_list(list_name, courses=None):
    """ return a list of projects
        if courses != None, only the courses in courses and the list
        will be returned.
    """
    course_ids = db.CourseListEntry.objects.filter(
        course_list__name = list_name
    ).values_list('course', flat=True)
    ret = _get_listed_courses().order_by("-date_added").filter(id__in=course_ids)
    if courses:
        ret.filter(url__in=[c.url for c in courses])
    return ret


# new course index API functions ->
def add_course_listing(course_url, title, description, data_url, language, thumbnail_url, tags):
    if _get_listed_courses().filter(url=course_url).exists():
        raise Exception("A course with that URL already exist. Try update?")
    course_listing_db = db.Course(
        title=title,
        description=description,
        url=course_url,
        data_url=data_url,
        language=language,
        thumbnail_url=thumbnail_url
    )
    course_listing_db.save()
    update_course_listing(course_url, tags=tags)
    #TODO schedule task to verify listing


def update_course_listing(course_url, title=None, description=None, data_url=None, language=None, thumbnail_url=None, tags=None):
    listing = _get_listed_courses().get(url=course_url)
    if title:
        listing.title = title
    if description:
        listing.description = description
    if data_url:
        listing.data_url = data_url
    if language:
        listing.language = language
    if thumbnail_url:
        listing.thumbnail_url = thumbnail_url
    listing.save()

    if tags:
        db.CourseTags.objects.filter(course=listing, internal=False).delete()
        for tag in tags:
            if not db.CourseTags.objects.filter(course=listing, tag=tag).exists():
                course_tag = db.CourseTags(tag=tag, course=listing)
                course_tag.save()


def search_course_title(keyword):
    return _get_listed_courses().order_by("-date_added").filter(title__istartswith=keyword)


def remove_course_listing(course_url):
    course_listing_db = _get_listed_courses().get(url=course_url)
    course_listing_db.date_removed = datetime.datetime.utcnow()
    course_listing_db.save()
    # TODO - what about lists that the course may be in?
    # Delete course tags
    course_listing_db.coursetags_set.all().delete()


def create_list(name, title, url):
    if db.List.objects.filter(name=name).exists():
        raise Exception("A list with that name already exists")

    course_list = db.List(
        name = name,
        title = title,
        url = url
    )
    course_list.save()


def add_course_to_list(course_url, list_name):
    try:
        course_list = db.List.objects.get(name=list_name)
    except:
        raise Exception("List doesn't exist")

    try:
        course = _get_listed_courses().get(url=course_url)
    except:
        raise Exception("Course at given URL doesn't exist")

    if db.CourseListEntry.objects.filter(course_list=course_list, course=course).exists():
        raise Exception("Course already in list")

    entry = db.CourseListEntry(
        course_list = course_list,
        course = course
    )
    entry.save()


def remove_course_from_list(course_url, list_name):
    try:
        course_list = db.List.objects.get(name=list_name)
    except:
        raise Exception("List doesn't exist")

    try:
        course = db.Course.objects.get(url=course_url)
    except:
        raise Exception("Course not in index")

    entry = db.CourseListEntry.objects.filter(course_list=course_list, course=course)

    if not entry.exists():
        raise Exception("Course not in list")

    entry.delete()


def get_lists_for_course(course_url):
    """ return all the lists that a course is in """
    try:
        course = _get_listed_courses().get(url=course_url)
    except:
        raise Exception("Course at given URL doesn't exist")

    return [
        {
            'name': l.course_list.name,
            'url': l.course_list.url,
            'title': l.course_list.title
        }
        for l in course.courselistentry_set.all()
    ]

