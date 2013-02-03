from django import http
from django.utils.translation import ugettext as _

from drumbeat import messages
from courses import models as course_model

def require_organizer( function ):
    def check_organizer( *args, **kwargs ):
        request = args[0]
        course_id = kwargs.get('course_id')
        course_uri = course_model.course_id2uri(course_id)
        user_uri = "/uri/user/{0}".format(request.user.username)
        cohort = course_model.get_course_cohort(course_uri)
        organizer = course_model.is_cohort_organizer(
            user_uri, cohort['uri']
        )
        organizer |= request.user.is_superuser
        if not organizer:
            return http.HttpResponseForbidden(_("You need to be a course organizer."))
        return function(*args, **kwargs)
    return check_organizer
