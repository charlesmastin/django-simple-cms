from django.contrib import admin
from django import forms
from django.contrib.sites.models import Site

from simple_cms.models import *

def action_set_active(modeladmin, request, queryset):
    queryset.update(active=True)

action_set_active.short_description = 'Make published'

def action_set_inactive(modeladmin, request, queryset):
    queryset.update(active=False)

action_set_inactive.short_description = 'Make un-published'

class NavigationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavigationForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs = {'cols':80, 'rows': 20}
        if len(Site.objects.all()) == 1:
            self.fields['site'].initial = Site.objects.all()[0]
        self.fields['format'].initial = 'markdown'

    class Meta:
        model = Navigation

class SeoInline(generic.GenericStackedInline):
    model = Seo
    extra = 0
    max_num = 1

class RelatedBlockInline(generic.GenericTabularInline):
    model = RelatedBlock
    extra = 0

class NavigationAdmin(admin.ModelAdmin):
    form = NavigationForm
    list_display = ['title', 'slug', 'order', 'parent', 'num_blocks', 'view', 'active']
    list_filter = ['group', 'site__name', 'active']
    save_on_top = True
    prepopulated_fields = {'slug': ('title',)}
    inlines = [RelatedBlockInline, SeoInline]
    search_fields = ['title', 'text']
    actions = [action_set_active, action_set_inactive]
    fieldsets = (
        (None, {
            'fields': (
                'active',
                ('title', 'slug'),
                ('site', 'group'),
                ('parent', 'order'),
                'text',
                'format',
            ),
        }),
        ('Advanced Options', {
            'classes': ('collapse',),
            'fields': (
                'page_title',
                'render_as_template',
                'homepage',
                'inherit_blocks',
                ('url', 'target'),
                ('view', 'template', 'inherit_template'),
                ('redirect_url', 'redirect_permanent'),
            ),
        }),
    )

class BlockAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'url', 'image', 'format')
    #list_filter = ('format', )
    actions = [action_set_active, action_set_inactive]
    fieldsets = (
        (None, {
            'fields': (
                'active',
                'key',
                'title',
                'image',
                ('url', 'target'),
                'text',
                'format',
            ),
        }),
        ('Advanced Options', {
            'classes': ('collapse',),
            'fields': (
                'render_as_template',
                'bypass_layout',
                'content_type',
                'object_id',
            ),
        }),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'order', 'active']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('title',)}
    actions = [action_set_active, action_set_inactive]

class CategoryInline(admin.TabularInline):
    model = Article.categories.through
    extra = 0

class ArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs = {'cols':80, 'rows': 20}
        self.fields['format'].initial = 'markdown'

    class Meta:
        model = Article

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm
    list_display = ['title', 'post_date', 'publish_start', 'publish_end', 'key_image', 'active']
    list_filter = ['active', 'categories']
    #date_hierarchy = 'post_date'
    prepopulated_fields = {'slug': ('title',)}
    save_on_top = True
    search_fields = ['title', 'text', 'excerpt']
    exclude = ['categories']
    inlines = [CategoryInline, SeoInline]
    actions = [action_set_active, action_set_inactive]
    fieldsets = (
        (None, {
            'fields': (
                'active',
                'post_date',
                ('title', 'slug'),
                'key_image',
                'text',
                'format',
                'tags',
                ('author', 'allow_comments'),
            ),
        }),
        ('Advanced Options', {
            'classes': ('collapse',),
            'fields': (
                'publish_start',
                'publish_end',
                'excerpt',
                'render_as_template',
                ('url', 'target'),
                'display_title',
                'display_image',
            ),
        }),
    )

admin.site.register(Block, BlockAdmin)
admin.site.register(BlockGroup)
admin.site.register(NavigationGroup)
admin.site.register(Navigation, NavigationAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
