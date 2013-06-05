from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from preferences.models import AccountPreferences
from preferences.models import set_notification_subscription
from projects.models import Participation

class Command(BaseCommand):
    help = 'Port AccountPreferences to NotificationSubscriptions'

    def handle(self, *args, **options):
        preference_to_category = {
            'no_email_message_received': 'direct-message',
            'no_email_new_follower': 'new-follower',
            'no_email_new_project_follower': 'course-signup',
            'no_email_new_badge_submission': 'badge-submission'
        }

        for preference in AccountPreferences.objects.all():
            set_notification_subscription(
                preference.user,
                preference_to_category[preference.key],
                False
            )

        unsubscribes = Participation.objects.filter(left_on__isnull=True).filter(
            Q(no_organizers_wall_updates=True) |
            Q(no_organizers_content_updates=True) |
            Q(no_participants_wall_updates=True) |
            Q(no_participants_content_updates=True)
        )

        for unsubscribe in unsubscribes:
            set_notification_subscription(
                unsubscribe.user,
                u'project-{0}'.format(unsubscribe.project.slug),
                False
            )
