from simple_cms.models import Navigation

def navigation(request):
    """ Look up matching request in navigation and use for pagebuilder """
    url = request.META['PATH_INFO']
    urlA = url.strip('/').split('/')
    
    page = None
    
    try:
        if urlA[0] == '':
            try:
                page = Navigation.objects.get(active=True, homepage=True)
            except Navigation.DoesNotExist:
                pass
    except:
        pass
    
    for slug in urlA:
        try:
            page = Navigation.objects.get(active=True, parent=page, slug=slug)
        except Navigation.DoesNotExist:
            break
    
    nav2 = []
    nav3 = None
    parent = None
    if page:
        # TODO: max template depth allowed, so hard code?
        if page.depth == 0:
            nav2 = list(page.children.all().filter(active=True).order_by('order'))
            parent = page
        if page.depth == 1:
            nav2 = list(page.parent.children.all().filter(active=True).order_by('order'))
            nav3 = list(page.children.all().filter(active=True).order_by('order'))
            nav3.insert(0, page)
            parent = page.parent
        if page.depth == 2:
            nav2 = list(page.parent.parent.children.all().filter(active=True).order_by('order'))
            nav3 = list(page.parent.children.all().filter(active=True).order_by('order'))
            nav3.insert(0, page.parent)
            parent = page.parent.parent
    
    return {
        'urlA': urlA,
        'page': page,
        'parent': parent,
        'nav2': nav2,
        'nav3': nav3,
    }

   