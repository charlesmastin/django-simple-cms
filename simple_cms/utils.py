import re

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.conf import settings

def render_with(template, logged_in_template=None):
    """
    Decorator for Django views that sends returned dict to render_to_response function
    with given template and RequestContext as context instance.
    
    From http://blog.vmfarms.com/2010/01/helpful-django-view-decorator-pattern.html
    
    """
    def renderer(func):
        def wrapper(request, *args, **kw):
            template_to_render = logged_in_template if logged_in_template and request.user.is_authenticated() else template
            
            output = func(request, *args, **kw)
            
            if isinstance(output, dict):
                return render_to_response(
                    template_to_render, output,
                    RequestContext(request, output))
            return output
        return wrapper
    return renderer
    
def send_email(header_subject, body, header_to, header_from=None, text_content=None):
    # we could throw this off into a thread, or use a queing system to improve performance
    if not header_from:
        header_from = settings.DEFAULT_FROM_EMAIL
    if not text_content:
        text_content = re.sub(r'<[^>]*?>', '', body)
    try:
        msg = EmailMultiAlternatives(header_subject, text_content, header_from, header_to)
        msg.attach_alternative(body, "text/html")
        msg.send()
    except:
        raise

def is_external_url(url, path):
    if url.find('http') != -1:
        try:
            # based on full URL
            if url.split('/')[2] != path.split('/')[2]:
                return True
        except:
            pass
    return False