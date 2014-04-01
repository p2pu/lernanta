from users.models import UserProfile
from courses.models import delete_spam_course, get_courses

def handle_spam_user(username):
    # delete user
    spammer = UserProfile.objects.get(username=username)
    spammer.user.set_unusable_password()
    spammer.user.save()
    spammer.deleted = True
    spammer.save()

    # delete user comments
    for spam in spammer.comments.all():
        spam.deleted = True
        spam.save()

    # delete courses created by user
    courses = get_courses(organizer_uri=u'/uri/user/{0}'.format(spammer.username))
    for course in courses:
        delete_spam_course(course['uri'])

