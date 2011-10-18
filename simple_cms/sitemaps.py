from django.contrib.sitemaps import Sitemap

from simple_cms.models import Navigation, Article

class NavigationSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0
    
    def items(self):
        return Navigation.objects.get_active()
    
    def lastmod(self, obj):
        return obj.updated_at


class ArticleSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.5
    
    def items(self):
        return Article.objects.get_active()
    
    def lastmod(self, obj):
        return obj.updated_at


