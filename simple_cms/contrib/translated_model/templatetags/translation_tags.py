from django.utils.safestring import mark_safe

from simple_cms.contrib.translated_model.models import LocalizationTranslation
from simple_cms.models import CommonAbstractModel
from django import template
register = template.Library()

@register.assignment_tag(takes_context=True)
def translate_instance(context, instance):
    try:
        code = context['request'].LANGUAGE_CODE
        if code != 'en-us':
            # now try to find a translation
            translations = instance.translations.filter(language__code=code)
            if len(translations):
                # map the non empty values on to the original instance
                translation = translations[0]
                # TODO: find out how to properly obtain the base classes up to models.Model and exclude all of their fields
                # TODO: find out how to properly obtain the PK fieldname
                excluded = CommonAbstractModel._meta.get_all_field_names() + ['id']
                for field in translation.__class__._meta.get_all_field_names():
                    if field not in excluded:
                        if field in instance.__class__._meta.get_all_field_names():
                            # also avoid reverse mapping generic name - kinda hard to exclude
                            try:
                                v = getattr(translation, field)
                                if v != translation.__class__._meta.get_field(field).default:
                                    setattr(instance, field, v)
                            except AttributeError:
                                pass
    except KeyError:
        pass
    return instance

@register.assignment_tag(takes_context=True)
def translated_field(context, instance, field):
    return translate_field(context, instance, field)

@register.simple_tag(takes_context=True)
def translate_field(context, instance, field):
    try:
        code = context['request'].LANGUAGE_CODE
        if code != 'en-us':
            # now try to find a translation
            translations = instance.translations.filter(language__code=code)
            if len(translations):
                p = getattr(translations[0], field)
                if len(p):
                    return p
    except KeyError:
        pass
    return getattr(instance, field)

@register.simple_tag(takes_context=True)
def translate_string(context, key, default):
    try:
        return mark_safe(LocalizationTranslation.objects.get(localization__name=key, language__code=context['request'].LANGUAGE_CODE).text)
    except LocalizationTranslation.DoesNotExist:
        if context['request'].LANGUAGE_CODE != 'en-us':
            try:
                return mark_safe(LocalizationTranslation.objects.get(localization__name=key, language__code='en-us').text)
            except LocalizationTranslation.DoesNotExist:
                return default
    return default