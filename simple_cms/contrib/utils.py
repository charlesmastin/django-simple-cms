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

def digg_paginator(records, ADJACENT_PAGES=3, BORDER_PAGES=2, BASE_RANGE=10):
    pages = []
    leading = []
    trailing = []
    
    # only 1 set
    if records.paginator.num_pages <= BASE_RANGE:
        # be sure to only rock the num of pages
        if records.paginator.num_pages > 1:
            pages = xrange(1, records.paginator.num_pages+1)
    # in the first range, with trailing
    elif records.paginator.num_pages > BASE_RANGE and records.number < BASE_RANGE+1:
        pages = xrange(1, BASE_RANGE+1)
        trailing = xrange(records.paginator.num_pages-BORDER_PAGES+1, records.paginator.num_pages+1)
    # within the end range
    elif records.paginator.num_pages - records.number <= ADJACENT_PAGES*2 + 1:
        leading = xrange(1, BORDER_PAGES+1)
        pages = xrange(records.paginator.num_pages-(ADJACENT_PAGES*2+1), records.paginator.num_pages+1)
    else:
        leading = xrange(1, BORDER_PAGES+1)
        pages = xrange(records.number - ADJACENT_PAGES, records.number + ADJACENT_PAGES+1)
        trailing = xrange(records.paginator.num_pages-BORDER_PAGES+1, records.paginator.num_pages+1)
    
    return {
        'pages': pages,
        'leading': leading,
        'trailing': trailing,
    }