import requests
import datetime

from celery.task import Task

from learn import db

class UpdateCourseTask(Task):
    """ Task to update and verify a course listing """
    name = 'learn.tasks.UpdateCourseTask'

    def run(self, course_url, **kwargs):
        listing = db.Courses.get(url=course_url)
        listing.date_checked = datetime.datetime.utcnow()
        listing.save()

        results = None
        if listing.data_url:
            # try to fetch data from course data_url
            try: 
                results = json.parse(request.get(listing.data_url))
            except:
                # could not fetch course data, verify that course still exists?
                pass

        if not results:
            # data_url is blank or failed, try to get LRMI metadata from url
            try:
                html = request.get(listing.url)
                #TODO
                listing.verified = True
                listing.save()
            except:
                pass

        if results:
            # update course data
            allowed_values = [
                'title', 'description', 'data_url', 'tags', 'language', 
                'thumbnail_url'
            ]
            args = {}
            for value in allowed_values:
                if value in results:
                    args[value] = results.get(value)
            from learn.models import update_course
            update_course_listing(course_url, **args)

            if listing.verified == False:
                try:
                    request.get(listing.url)
                    listing.verified = True
                    listing.save()
                except:
                    pass
        else:
            listing.verified = False
            listing.save()

