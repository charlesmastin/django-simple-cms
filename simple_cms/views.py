from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.conf import settings


from simple_cms.models import Navigation

def page(request, template=''):
    if template == '':
        template = settings.SIMPLE_CMS_PAGE_TEMPLATE
    context = RequestContext(request)
    for i in context['pageA']:
        if i.template:
            template = i.template
    if context['page'].view:
        # dynamic import, not a terrible risk
        tA = context['page'].view.split('.')
        c = tA.pop()
        import_string = 'from %s import %s' % ('.'.join(tA), c)
        exec import_string
        return eval(c)(request=request)
    return render_to_response(
        template,
        { },
        context_instance=RequestContext(request)
    )