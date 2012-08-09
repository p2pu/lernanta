from django.http import Http404
from django.conf import settings

class APISubdomainMiddleware:
    def process_request(self, request):
        """Parse out the subdomain from the request and redirect to API"""

        host = request.META.get('HTTP_HOST', '')
        host_s = host.replace('www.', '').split('.')

        if ((host_s[0] != 'api') and request.path.startswith('/alpha')):
            request.session = {} #TODO - fix middleware depending on session
            raise Http404

        if ((host_s[0] == 'api') and not request.path.startswith('/alpha')):
            request.session = {} #TODO - fix middleware depending on session
            raise Http404

        return None
