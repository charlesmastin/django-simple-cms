from django.contrib import admin

from simple_cms.contrib.translated_model.models import *

class LocalizationTranslationAdmin(admin.ModelAdmin):
    list_display = ['localization', 'language', 'text']
    list_filter = ['language']

admin.site.register(Language)
admin.site.register(Localization)
admin.site.register(LocalizationTranslation, LocalizationTranslationAdmin)