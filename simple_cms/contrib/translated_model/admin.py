from django.contrib import admin

from simple_cms.contrib.translated_model.models import *
from simple_cms.admin import action_set_active, action_set_inactive

class LanguageAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'display_name', 'order', 'active']
	list_filter = ['active']
	actions = [action_set_active, action_set_inactive]

class LocalizationTranslationAdmin(admin.ModelAdmin):
    list_display = ['localization', 'language', 'text']
    list_filter = ['language']

admin.site.register(Language, LanguageAdmin)
admin.site.register(Localization)
admin.site.register(LocalizationTranslation, LocalizationTranslationAdmin)