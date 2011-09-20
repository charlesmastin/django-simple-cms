from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from simple_cms.models import Article
from sorl.thumbnail import get_thumbnail
import os
import mimetypes

class ArticleFeed(Feed):
    title = ''
    description = ''

    def item_pubdate(self, item):
        return item.post_date

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        if item.excerpt:
            return item.excerpt
        else:
            return item.text[:300]

    def item_enclosure_url(self, item):
        if item.key_image and item.display_image:
            return item.key_image.url

    def item_enclosure_length(self, item):
        if item.key_image and item.display_image:
            return os.path.getsize('%s' % item.key_image.file)

    def item_enclosure_mime_type(self, item):
        if item.key_image and item.display_image:
            return mimetypes.guess_type('%s' % item.key_image.file)

    def items(self):
        return Article.objects.get_active()[:30]
    