from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import logout

from users.models import UserProfile
from l10n.urlresolvers import reverse


class ProfileExistMiddleware(object):

    def process_request(self, request):
        if not request.user.is_authenticated():
            return
        try:
            profile = request.user.get_profile()
            if profile.deleted == True:
                logout(request)
                return HttpResponseRedirect(reverse('splash'))
        except UserProfile.DoesNotExist:
            dashboard_url = reverse('dashboard')
            profile_create_url = reverse('users_profile_create')
            logout_url = reverse('users_logout')
            check_username_url = reverse('users_check_username')
            valid_urls = (dashboard_url, profile_create_url, logout_url, check_username_url)
            if request.path in valid_urls:
                return None
            for prefix in settings.NO_PROFILE_URLS:
                if request.path.startswith(prefix):
                    return None
            return HttpResponseRedirect(dashboard_url)
