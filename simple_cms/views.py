from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings

from simple_cms.models import Navigation

def page(request, template=''):
    url = request.META['PATH_INFO']
    urlA = url.strip('/').split('/')
    if template == '':
        template = settings.SIMPLE_CMS_PAGE_TEMPLATE
    page = None
    for slug in urlA:
        page = get_object_or_404(Navigation, parent=page, slug=slug, active=True)
        if page.template:
            template = page.template
    if page.view:
        # dynamic import, not a terrible risk
        tA = page.view.split('.')
        c = tA.pop()
        import_string = 'from %s import %s' % ('.'.join(tA), c)
        exec import_string
        return eval(c)(request=request)
    return render_to_response(
        template,
        { },
        context_instance=RequestContext(request)
    )