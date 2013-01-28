from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from projects.models import Project
from schools.models import School
from signups.models import Signup
from learn.models import add_course_listing
from learn.models import update_course_listing
from learn.models import create_list
from learn.models import add_course_to_list


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        listed = Project.objects.filter(
            not_listed=False,
            deleted=False,
            archived=False,
            test=False
        )

        # create lists for schools
        for school in School.objects.all():
            try:
                create_list(
                    school.slug, school.name, 
                    "http://p2pu.org/en/schools/{0}".format(school.slug)
                )
            except:
                pass

            try:
                create_list(
                    "{0}_featured".format(school.slug),
                    "{0} featured".format(school.name),
                    "http://p2pu.org/en/schools/{0}".format(school.slug)
                )
            except:
                pass

        # create list for listed courses
        try:
            create_list("listed", "Listed courses", "")
        except:
            pass

        # create list for draft courses
        try:
            create_list("drafts", "Draft courses", "")
        except:
            pass


        listed = listed.filter(
            Q(category=Project.CHALLENGE)
            | Q(sign_up__status=Signup.MODERATED)
            | Q(sign_up__status=Signup.NON_MODERATED)
        )

        listed = listed.order_by('created_on')

        for project in listed:
            project_tags = project.tags.all().values_list('name', flat=True)
            args = dict(
                course_url = "/en/groups/{0}/".format(project.slug),
                title = project.name,
                description = project.short_description,
                data_url = "/en/groups/{0}/data".format(project.slug),
                language = project.language,
                thumbnail_url = "http://p2pu.org{0}".format(project.get_image_url()),
                tags = project_tags
            )
            try:
                add_course_listing(**args)
            except:
                update_course_listing(**args)

            if project.under_development == True:
                try:
                    add_course_to_list(args["course_url"], "drafts")
                except:
                    pass
            else:
                try:
                    add_course_to_list(args["course_url"], "listed")
                except:
                    pass

            if project.school:
                try:
                    add_course_to_list(args['course_url'], project.school.slug)
                except:
                    pass

        # create lists
        try:
            create_list('community', "Community Picks", "")
        except:
            pass

        try:
            create_list('showcase', "Showcased", "")
        except:
            pass

        for project in listed.filter(community_featured=True):
            course_url = "/en/groups/{0}/".format(project.slug)
            try:
                add_course_to_list(course_url, 'community')
            except:
                pass

        for project in listed.filter(featured=True):
            course_url = "/en/groups/{0}/".format(project.slug)
            add_course_to_list(course_url, 'showcase')

        for school in School.objects.all():
            for project in school.featured.all():
                course_url = "/en/groups/{0}/".format(project.slug)
                list_name = "{0}_featured".format(school.slug)
                try:
                    add_course_to_list(course_url, list_name)
                except:
                    pass

