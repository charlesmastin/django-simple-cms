from django.contrib.sites.models import Site
from django.conf import settings

from simple_cms.models import Navigation

class NavigationHelper(object):
    
    def __init__(self, request):
        self.request = request
        self.urlA = request.META['PATH_INFO'].strip('/').split('/')
        self.page = None
        self.pageA = []
        self.nav2 = None
        self.nav3 = None
        self.parent = None
        try:
            self.site = Site.objects.get_current()
        except:
            self.site = Site.objects.get(pk=1)
        self.insert_parent = True
    
    def is_homepage(self):
        try:
            if self.urlA[0] == '':
                try:
                    self.page = Navigation.objects.get(active=True, site=self.site, homepage=True)
                    self.pageA.append(self.page)
                    return True
                except Navigation.DoesNotExist:
                    return False
        except:
            return False
        return False
    
    def find_page(self):
        for slug in self.urlA:
            try:
                self.page = Navigation.objects.get(active=True, parent=self.page, slug=slug, site=self.site)
                self.pageA.append(self.page)
            except Navigation.DoesNotExist:
                break
    
    def define_nav(self):
        if self.page:
            # TODO: max template depth allowed, so hard code?
            if self.page.depth == 0:
                self.nav2 = list(self.page.children.all().filter(active=True).order_by('order'))
                self.parent = self.page
            if self.page.depth == 1:
                self.nav2 = list(self.page.parent.children.all().filter(active=True).order_by('order'))
                self.nav3 = list(self.page.children.all().filter(active=True).order_by('order'))
                if self.insert_parent:
                    self.nav3.insert(0, self.page)
                self.parent = self.page.parent
            if self.page.depth == 2:
                self.nav2 = list(self.page.parent.parent.children.all().filter(active=True).order_by('order'))
                self.nav3 = list(self.page.parent.children.all().filter(active=True).order_by('order'))
                if self.insert_parent:
                    self.nav3.insert(0, self.page.parent)
                self.parent = self.page.parent.parent
    
    def extra_context(self):
        return None
    
    def context(self):
        r = {
            'urlA': self.urlA,
            'page': self.page,
            'pageA': self.pageA,
            'parent': self.parent,
            'nav2': self.nav2,
            'nav3': self.nav3,
        }
        if self.extra_context():
            r.update(self.extra_context())
        return r

def navigation(request):
    """ Look up matching request in navigation and use for pagebuilder """
    try:
        module = settings.SIMPLE_CMS_CONTEXT_PROCESSOR
        tA = module.split('.')
        c = tA.pop()
        import_string = 'from %s import %s' % ('.'.join(tA), c)
        exec import_string
        cls = eval(c)
    except (AttributeError, ImportError):
        cls = NavigationHelper
    inst = cls(request)
    if inst.is_homepage():
        pass
    else:
        inst.find_page()
    inst.define_nav()
    return inst.context()

   