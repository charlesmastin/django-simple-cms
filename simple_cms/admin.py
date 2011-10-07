from django.contrib import admin
from django import forms

from models import *

class BlockInline(admin.TabularInline):
    model = NavigationBlocks
    extra = 0

class NavigationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavigationForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs = {'cols':80, 'rows': 20}

    class Meta:
        model = Navigation

class NavigationAdmin(admin.ModelAdmin):
    form = NavigationForm
    list_display = ['title', 'slug', 'order', 'parent', 'blocks', 'view', 'active']
    list_filter = ['group', 'site__name', 'active']
    save_on_top = True
    prepopulated_fields = {'slug': ('title',)}
    inlines = [BlockInline]
    search_fields = ['title', 'text']
    fieldsets = (
        (None, {
            'fields': (
                'active',
                ('title', 'slug'),
                ('group', 'parent', 'order'),
                'site',
                'text',
                'format',
            ),
        }),
        ('SEO / Advanced Options', {
            'classes': ('collapse',),
            'fields': (
                'seo_title',
                'seo_description',
                'seo_keywords',
                'page_title',
                'homepage',
                'inherit_blocks',
                'render_as_template',
                ('url', 'target'),
                ('view', 'template'),
                ('redirect_url', 'redirect_permanent'),
            ),
        }),
    )

class BlockAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'image', 'format')
    list_filter = ('format', )
    fieldsets = (
        (None, {
            'fields': (
                'active',
                'key',
                'title',
                'image',
                'text',
                'format',
            ),
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': (
                'render_as_template',
                'content_type',
                'object_id',
            ),
        }),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'order', 'active']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('title',)}


class CategoryInline(admin.TabularInline):
    model = Article.categories.through
    extra = 0

class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'post_date', 'has_excerpt', 'active']
    list_filter = ['active', 'post_date']
    date_hierarchy = 'post_date'
    prepopulated_fields = {'slug': ('title',)}
    save_on_top = True
    exclude = ['categories']
    inlines = [CategoryInline]

admin.site.register(Block, BlockAdmin)
admin.site.register(BlockGroup)
admin.site.register(NavigationGroup)
admin.site.register(Navigation, NavigationAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
