from django.http import HttpResponseRedirect
from django.utils.translation.trans_real import parse_accept_lang_header
from django.conf import settings

from simple_cms.contrib.translated_model.models import Language

class LanguageMiddleware(object):
    """
    Transparently check and set language preference...
    based initially on browser locale
    then on cookie value, which is user-overrideable
    """
    
    def process_request(self, request):
        # do we have a session?
        code = request.session.get('language')
        if code:
            request.LANGUAGE_CODE = code
            try:
                code = request.GET['language']
                request.session['language'] = code
                # this is prolly uncessesary
                request.LANGUAGE_CODE = code
                # do a redirect so we ditch the GET variable
                return HttpResponseRedirect(request.META['PATH_INFO'])
            except KeyError:
                pass
        else:
            # if no session, do we have browser locale?
            request.LANGUAGE_CODE = settings.DEFAULT_LANGUAGE
            try:
                locales = parse_accept_lang_header(request.META['HTTP_ACCEPT_LANGUAGE'])
                # try to find a match. Check first item primarily
                language = None
                for locale in locales:
                    if not language:
                        # check for presense of - (do we have full locale or just language)
                        if locale[0].rfind('-') == -1:
                            try:
                                language = Language.objects.get(active=True, code__istartswith=locale[0])
                                request.LANGUAGE_CODE = language.code
                            except Language.DoesNotExist:
                                pass
                        else:
                            try:
                                language = Language.objects.get(active=True, code__iexact=locale[0])
                                request.LANGUAGE_CODE = language.code
                            except Language.DoesNotExist:
                                pass
            except KeyError:
                pass
            request.session['language'] = request.LANGUAGE_CODE