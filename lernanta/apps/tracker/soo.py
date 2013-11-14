from disqus import utils
from courses import models as course_model
from projects.models import Project

def get_stats():
    course_list = [ 632, 667, 620, 5, 77, 588, 140, 3 ]
    stats = []
    
    for course_id in course_list:
        course = course_model.get_course('/uri/course/{0}'.format(course_id))

        for content in course['content']:
            ident = '{0}-{1}'.format(course_id, content['id'])
            thread = utils.get_thread(ident)
            stats += [ (course['title'], content['title'], thread['response']['posts'] ) ]
            print('https://p2pu.org/en/courses/{0}, "{1}", {2}'.format(course_id, content['title'], thread['response']['posts']))

    old_course_list = [
        'get-cc-savvy',
        'teach-someone-something-with-open-content',
        'teach-someone-something-with-open-content-part-2',
        'open-detective',
        'contributing-to-wikimedia-commons',
        'open-glam',
        'a-look-at-open-video',
        'make-something-with-the-daily-create',
        'dscribe-peer-produced-open-educational-resources',
        'open-access-wikipedia-challenge'
    ]


    for course_slug in old_course_list:
        project = Project.objects.get(slug=course_slug)
        for page in project.pages.filter(deleted=False, listed=True):
            stats += [ ('https://p2pu.org/en/groups/{0}'.format(course_slug), page.title, page.comments.count()) ]
            print('https://p2pu.org/en/groups/{0}, "{1}", {2}'.format(course_slug, page.title, page.comments.count()))

    return stats
