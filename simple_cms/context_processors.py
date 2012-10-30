from django.contrib.sites.models import Site, RequestSite
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
        self.nav2_parent = None
        self.nav3_parent = None
        self.exact_match = False
        try:
            self.check_domain = settings.SIMPLE_CMS_CHECK_DOMAIN
        except:
            self.check_domain = False
        if self.check_domain:
            try:
                self.site = Site.objects.get(domain=RequestSite(request).domain)
            except:
                self.site = Site.objects.get(pk=1)
        else:
            try:
                self.site = Site.objects.get_current()
            except:
                self.site = Site.objects.get(pk=1)
    
    def is_homepage(self):
        try:
            if self.urlA[0] == '':
                try:
                    kwargs = {'active':True, 'homepage':True}
                    if self.check_domain and self.site:
                        kwargs['site'] = self.site
                    self.page = Navigation.objects.get(**kwargs)
                    self.pageA.append(self.page)
                    self.exact_match = True
                    return True
                except Navigation.DoesNotExist:
                    return False
        except:
            return False
        return False
    
    def find_page(self):
        admin_preview = False
        try:
            admin_preview = self.request.GET.get('admin_preview')
            if admin_preview:
                if not self.request.user.is_authenticated or not self.request.user.is_staff:
                    return
        except KeyError:
            pass
        for slug in self.urlA:
            try:
                kwargs = {'active': True, 'parent':self.page, 'slug':slug}
                if admin_preview:
                    del kwargs['active']
                if self.check_domain and self.site:
                    kwargs['site'] = self.site
                self.page = Navigation.objects.get(**kwargs)
                self.pageA.append(self.page)
            except Navigation.DoesNotExist:
                break
        # check for exact match, need to ignore the trailing anchors and so on, so reassemble the
        if self.page:
            if self.page.get_absolute_url() == '/%s/' % '/'.join(self.urlA):
                self.exact_match = True
    
    def define_nav(self):
        if self.page:
            # TODO: max template depth allowed, so hard code?
            if self.page.depth == 0:
                self.parent = self.page
                self.nav2 = list(self.page.children.all().filter(active=True).order_by('order'))
                self.nav2_parent = self.page
            if self.page.depth == 1:
                self.parent = self.page.parent
                self.nav2 = list(self.page.parent.children.all().filter(active=True).order_by('order'))
                self.nav2_parent = self.page.parent
                self.nav3 = list(self.page.children.all().filter(active=True).order_by('order'))
                self.nav3_parent = self.page
            if self.page.depth == 2:
                self.parent = self.page.parent.parent
                self.nav2 = list(self.page.parent.parent.children.all().filter(active=True).order_by('order'))
                self.nav2_parent = self.page.parent.parent
                self.nav3 = list(self.page.parent.children.all().filter(active=True).order_by('order'))
                self.nav3_parent = self.page.parent
    
    def extra_context(self):
        return None
    
    def context(self):
        r = {
            'site': self.site,
            'urlA': self.urlA,
            'page': self.page,
            'pageA': self.pageA,
            'parent': self.parent,
            'nav2': self.nav2,
            'nav2_parent': self.nav2_parent,
            'nav3': self.nav3,
            'nav3_parent': self.nav3_parent,
            'exact_match': self.exact_match,
        }
        if self.page:
            if len(self.page.seo.all()) == 1:
                r.update({'seo': self.page.seo.all()[0]})
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

   