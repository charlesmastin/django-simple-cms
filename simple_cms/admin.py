from django.contrib import admin

from models import *

class BlockInline(admin.TabularInline):
    model = NavigationBlocks
    extra = 0

class NavigationAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'order', 'slug', 'group', 'view', 'active']
    list_filter = ['group', 'active']
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
            ),
        }),
    )

class BlockAdmin(admin.ModelAdmin):
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
                'content_type',
                'object_id',
            ),
        }),
    )

admin.site.register(Block, BlockAdmin)
admin.site.register(BlockGroup)
admin.site.register(NavigationGroup)
admin.site.register(Navigation, NavigationAdmin)
