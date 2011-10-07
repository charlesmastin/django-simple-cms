from simple_cms.models import Navigation
from simple_cms.views import NavigationView
from django.http import Http404
from django.conf import settings
from django.utils.functional import update_wrapper

class NavigationMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        try:
            view = NavigationView().dispatch(request)
            update_wrapper(view, NavigationView, updated=())
            update_wrapper(view, NavigationView.dispatch, assigned=())
            return view
        except Http404:
            return response
        except:
            if settings.DEBUG:
                raise
            return response