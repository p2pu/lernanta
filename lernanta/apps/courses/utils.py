import courses.models as course_model
import content2.models as content_model
from content2 import utils as content_utils

def import_project(project, hashtag):
    course = {}
    course['title'] = project.name
    course['hashtag'] = hashtag
    course['description'] = project.short_description
    course['language'] = project.language
    user_uri = "/uri/user/{0}".format(project.participations.filter(organizing=True).order_by('joined_on')[0].user.username)
    course['organizer_uri'] = user_uri

    course = course_model.create_course(**course)

    # update about page
    about = {
        "uri": course['about_uri'],
        "title": "About",
        "content": project.long_description,
        "author_uri": user_uri,
    }
    content_model.update_content(**about)

    # add other pages to course
    for page in project.pages.filter(deleted=False, listed=True).order_by('index'):
        content = {
            "title": page.title,
            "content": content_utils.clean_user_content(page.content),
            "author_uri": "/uri/user/{0}".format(page.author.username),
        }
        content = content_model.create_content(**content)
        course_model.add_course_content(course['uri'], content['uri'])

    return course
