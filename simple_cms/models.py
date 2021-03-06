import datetime

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.encoding import *
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.sites.models import Site
from django.db.models import Q

from django.conf import settings

from django_extensions.db.fields import CreationDateTimeField
from django_extensions.db.fields import ModificationDateTimeField
from django_extensions.db.fields import AutoSlugField
from taggit.managers import TaggableManager
from positions.fields import PositionField

FORMAT_CHOICES = (
    ('html', 'html'),
    ('markdown', 'markdown'),
    ('textile', 'textile'),
    ('restructuredtext', 'restructuredtext')
)

TARGET_CHOICES = (
    ('_blank', '_blank'),
    ('_self', '_self'),
    ('_top', '_top'),
    ('_parent', '_parent')
)

class CommonAbstractManager(models.Manager):

    def get_active(self):
        return self.all().filter(active=True)

class TextMixin(object):
    def get_text_block(self):
        return {
            'text': self.text,
            'format': self.format,
            'render_as_template': self.render_as_template,
        }

class UrlMixin(object):
    @property
    def link_attributes(self):
        r = ''
        if self.target:
            r = r+'target="%s"' % self.target
        if self.url:
            r = r+'href="%s"' % self.url
            return mark_safe(r)
        return mark_safe(r)

class CommonAbstractModel(models.Model):
    """
    Common ABC for most models.
    Provides created/updated_at, and active/inactive status.
    """
    created_at = CreationDateTimeField()
    updated_at = ModificationDateTimeField()
    active = models.BooleanField(default=True, verbose_name="published")
    objects = CommonAbstractManager()

    class Meta:
        get_latest_by = 'updated_at'
        ordering = ('-updated_at', '-created_at')
        abstract = True

    def get_class_name(self):
        return self.__class__.__name__

class Seo(models.Model):
    title = models.CharField(max_length=255, blank=True, default='', help_text='Complete html title replacement')
    description = models.TextField(blank=True, default='')
    keywords = models.TextField(blank=True, default='')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ['content_type', 'object_id']
        verbose_name_plural = 'Seo'

    def __unicode__(self):
        return u'%s' % self.id

class BlockGroup(models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return u'%s' % self.title

class Block(TextMixin, UrlMixin, CommonAbstractModel):
    key = models.CharField(max_length=255, unique=True, help_text='Internal name to refer to this item')
    title = models.CharField(max_length=255, blank=True, help_text='Optional header on sidebar')
    text = models.TextField(blank=True, default='')
    format = models.CharField(max_length=255, blank=True, default='', choices=FORMAT_CHOICES)
    render_as_template = models.BooleanField(default=False)
    image = models.ImageField(upload_to='uploads/contentblocks/', blank=True, default='', help_text='Optional image')
    url = models.CharField(max_length=255, blank=True, default='', help_text='eg. link image / title somewhere http://awesome.com/ or /awesome/page/')
    target = models.CharField(max_length=255, blank=True, default='', help_text='eg. open image / title link in "_blank" window', choices=TARGET_CHOICES)
    bypass_layout = models.BooleanField(default=False, help_text='Render only text field content, no surrounding markup.')

    # consider ditching these - NOW
    content_type = models.ForeignKey(ContentType, blank=True, null=True, help_text="""Choose an existing item type.<br>The most common choices will be Expert, etc.""")
    object_id = models.PositiveIntegerField(blank=True, null=True, help_text="""Type in the ID of the item you want to choose. You should see the title appear beside the box.""")
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u'%s' % (self.key)

class RelatedBlock(CommonAbstractModel):
    """ Linking Blocks to any object """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    block = models.ForeignKey('simple_cms.Block')
    group = models.ForeignKey('simple_cms.BlockGroup', blank=True, null=True)
    order = PositionField(collection=('content_type', 'object_id', 'group'))
    """ Because of the crummy status of the PositionField among other complications
    (leaving the content_type null and PositionField collection dependency)
    it is necessary to maintain a separate model for arbitrary grouping of blocks,
    eg, objects that don't necessarily map to a page, or page hierchy so simply,
    instead using the BlockGroup to unite them
    """


    class Meta:
        ordering = ['order', ]

    def __unicode__(self):
        return u'%s - %s' % (self.content_object, self.block)

class NavigationGroup(models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return u'%s' % self.title

class Navigation(TextMixin, CommonAbstractModel):
    """
    Navigation and Page combined model
    Customizations on One-To-One in implementing app
    """
    title = models.CharField(max_length=255, help_text='Navigation and default page title')
    slug = AutoSlugField(editable=True, populate_from='title')
    group = models.ForeignKey(NavigationGroup, blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    order = PositionField(collection=('parent', 'site'))
    site = models.ForeignKey(Site, related_name='pages')
    homepage = models.BooleanField(default=False)
    url = models.CharField(max_length=255, blank=True, default='', help_text='eg. link somewhere else http://awesome.com/ or /awesome/page/')
    target = models.CharField(max_length=255, blank=True, default='', help_text='eg. open link in "_blank" window', choices=TARGET_CHOICES)
    page_title = models.CharField(max_length=255, blank=True, default='', help_text='Optional html title')
    text = models.TextField(blank=True, default='')
    format = models.CharField(max_length=255, blank=True, default='', choices=FORMAT_CHOICES)
    render_as_template = models.BooleanField(default=False)
    template = models.CharField(max_length=255, blank=True, default='', help_text='Eg. common/awesome.html')
    view = models.CharField(max_length=255, blank=True, default='', help_text='Eg. common.views.awesome')
    redirect_url = models.CharField(max_length=255, blank=True, default='')
    redirect_permanent = models.BooleanField(default=False)
    inherit_blocks = models.BooleanField(default=True, verbose_name="Inherit Blocks")
    inherit_template = models.BooleanField(default=False, verbose_name="Inherit Template")
    seo = GenericRelation(Seo)
    blocks = GenericRelation(RelatedBlock)

    class Meta:
        unique_together = (('site', 'slug', 'parent'),)
        ordering = ['title']
        verbose_name_plural = 'Navigation'

    def __unicode__(self):
        return u'%s' % self._chain()

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.parent == self:
            raise ValidationError('Can\'t set parent to self.')

    def num_blocks(self):
        l = len(self.blocks.all())
        if l:
            return l
        return ''

    def custom_template(self):
        if self.template:
            return '<img src="%sadmin/img/icon-yes.gif" alt="yes" title="%s">' % (settings.STATIC_URL, self.template)
        return ''
    custom_template.allow_tags = True
    custom_template.admin_order_field = 'template'

    def custom_view(self):
        if self.view:
            return '<img src="%sadmin/img/icon-yes.gif" alt="yes" title="%s">' % (settings.STATIC_URL, self.view)
        return ''
    custom_view.allow_tags = True
    custom_view.admin_order_field = 'view'

    def root(self):
        item = self
        while item.parent:
            item = item.parent
        return item

    def get_title(self):
        if self.page_title:
            return self.page_title
        return self.title

    def _chain(self, prop='title'):
        """ Create slug chain for an object and its parent(s). """
        item = self
        tA = [getattr(item, prop)]
        while item.parent:
            item = item.parent
            tA.append(getattr(item, prop))
        else:
            pass
        tA.reverse()
        return '/'.join(['%s' % name for name in tA])

    def get_absolute_url(self):
        if self.url:
            return self.url
        return mark_safe('/%s/' % self._chain('slug'))

    def get_children(self):
        return self.children.all().filter(active=True).order_by('order')

    @property
    def href(self):
        r = ''
        if self.target:
            r = r+'target="%s"' % self.target
        if self.url:
            r = r+'href="%s"' % self.url
            return mark_safe(r)
        r = r+'href="/%s/"' % self._chain('slug')
        return mark_safe(r)

    @property
    def link_attributes(self):
        return self.href

    @property
    def depth(self):
        depth = 0
        item = self
        while item.parent:
            item = item.parent
            depth += 1
        else:
            pass
        return depth

    @property
    def search_description(self):
        return self.text

class Category(CommonAbstractModel):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(editable=True, populate_from='title')
    order = PositionField(collection='parent')
    parent = models.ForeignKey('self', blank=True, null=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['title']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return u'%s' % self.title

class PublishedManager(CommonAbstractManager):

    def get_published(self):
        return self.get_active().filter(Q(publish_start__lte=datetime.datetime.now(), publish_end=None) | Q(publish_start__lte=datetime.datetime.now(), publish_end__gte=datetime.datetime.now()))

class Article(TextMixin, UrlMixin, CommonAbstractModel):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(editable=True, populate_from='title')
    # default to now
    post_date = CreationDateTimeField(editable=True, help_text='Display Date')#models.DateTimeField(auto_now_add=True, editable=True, blank=True, help_text='Display Date')
    text = models.TextField(blank=True, default='')
    format = models.CharField(max_length=255, blank=True, default='', choices=FORMAT_CHOICES)
    render_as_template = models.BooleanField(default=False)
    excerpt = models.TextField(blank=True, default='')
    key_image = models.ImageField(upload_to='uploads/blog/', blank=True, default='')
    display_image = models.BooleanField(default=True, blank=True, help_text='Display image on post detail?')
    tags = TaggableManager(blank=True)
    categories = models.ManyToManyField('simple_cms.Category', blank=True, related_name='articles')
    allow_comments = models.BooleanField(default=True)
    sticky = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, default='', help_text='eg. link somewhere else http://awesome.com/ or /awesome/page/')
    target = models.CharField(max_length=255, blank=True, default='', help_text='eg. open link in "_blank" window', choices=TARGET_CHOICES)
    display_title = models.BooleanField(default=True, help_text='Display title on list view?')
    publish_start = CreationDateTimeField(editable=True, help_text='Show active content starting at this time.')
    publish_end = models.DateTimeField(null=True, blank=True, help_text='Stop publishing active content at the time.')
    objects = PublishedManager()

    seo = GenericRelation(Seo)
    blocks = GenericRelation(RelatedBlock)



    class Meta:
        ordering = ['-post_date']

    def __unicode__(self):
        return u'%s' % self.title

    def has_excerpt(self):
        if self.excerpt != '':
            return '<img src="%sadmin/img/icon-yes.gif" alt="True">' % settings.STATIC_URL
        return '<img src="%sadmin/img/icon-no.gif" alt="False">' % settings.STATIC_URL

    has_excerpt.admin_order_field = 'excerpt'
    has_excerpt.allow_tags = True

    def get_target(self):
        if self.target:
            return 'target="%s"' % self.target
        return ''

"""
class Venue(CommonAbstractModel):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(editable=True, populate_from='name')
    url = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    city = models.CharField(max_length=255, blank=True, default='')
    state = models.CharField(max_length=255, blank=True, default='')
    country = CountryField(default='US')
    address = models.CharField(max_length=255, blank=True, default='')
    address_extended = models.CharField(max_length=255, blank=True, default='')
    postal_code = models.CharField(max_length=255, blank=True, default='')
    gmt_offset = models.CharField(max_length=255, blank=True, default='', help_text='Eg. -07:00')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % self.name

    @property
    def map_address(self):
        tA = []
        if self.location_city:
            tA.append(self.location_city)
        if self.location_state:
            tA.append(self.location_state)
        tA.append(self.location_country.code)
        return ', '.join(tA)


class EventManager(models.Manager):

    def get_active(self):
        return self.get_query_set().filter(active=True)

    def upcoming(self):
        return self.get_active().filter(start_datetime__gte=datetime.date.today())

    def past(self):
        return self.get_active().filter(start_datetime__lte=datetime.date.today()).order_by('-start_datetime')


class Event(TextMixin, CommonAbstractModel):
    title = models.CharField(max_length=255, blank=True, default='')
    slug = AutoSlugField(editable=True, populate_from=('title'), allow_duplicates=True)
    start_datetime = models.DateTimeField(verbose_name="Event Starts on",
        help_text="Date format, YYY-MM-DD. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Time format, HH:MM:SS (24-hour clock)<br>Enter time as local to the event.",
        blank=True, null=True)
    end_datetime = models.DateTimeField(verbose_name="Event Ends on",
        help_text="Date format, YYY-MM-DD. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Time format, HH:MM:SS (24-hour clock)<br>Enter time as local to the event.",
        blank=True, null=True)
    display_time = models.BooleanField(default=True)
    venue = models.ForeignKey(Venue)
    text = models.TextField(blank=True, default='')
    format = models.CharField(max_length=255, blank=True, default='', choices=FORMAT_CHOICES)
    render_as_template = models.BooleanField(default=False)
    excerpt = models.TextField(blank=True, default='')
    key_image = models.ImageField(upload_to='uploads/events/', blank=True, default='')
    tickets_url = models.CharField(max_length=255, blank=True, default='')
    tags = TaggableManager(blank=True)
    objects = EventManager()

    class Meta:
        ordering = ['start_datetime', 'end_datetime']

    def __unicode__(self):
        return u'%s' % (self.pk)

    @property
    def is_past(self):
        now = datetime.datetime.now()

        if self.end_datetime:
            if (self.end_datetime > now):
                return False
            else:
                return True
        elif self.start_datetime:
            if (self.start_datetime < now):
                return True
            else:
                return False
        else:
            return True

    @property
    def spanning(self):
        if self.end_datetime:
            if self.end_datetime.date() != self.start_datetime.date():
                return True
        return False
"""
