from simple_cms.models import Navigation
from simple_cms.views import page
from django.http import Http404
from django.conf import settings

class NavigationMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        try:
            return page(request)
        except Http404:
            return response
        except:
            if settings.DEBUG:
                raise
            return response