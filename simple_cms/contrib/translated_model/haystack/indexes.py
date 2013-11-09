from haystack import indexes
from simple_cms.contrib.translated_model.haystack.fields import MultiLanguageCharField
from haystack.utils import get_identifier
from haystack.constants import ID, DJANGO_CT, DJANGO_ID
from django.utils.encoding import force_unicode


class MultiLanguageIndex(indexes.SearchIndex):
    language = indexes.CharField()
    text = MultiLanguageCharField(document=True, use_template=True)
    
    def prepare(self, obj, language):
        self.prepared_data = {
            ID: '%s.%s' % (get_identifier(obj), language.code),
            DJANGO_CT: "%s.%s" % (obj._meta.app_label, obj._meta.module_name),
            DJANGO_ID: force_unicode(obj.pk),
        }
        for field_name, field in self.fields.items():
            # Use the possibly overridden name, which will default to the
            # variable name of the field.
            self.prepared_data[field.index_fieldname] = field.prepare(obj)

            if field.use_template and field.document:
                try:
                    self.prepared_data[field.index_fieldname] = field._prepare_template(obj, language)
                except:
                    pass

            if hasattr(self, "prepare_%s" % field_name):
                value = getattr(self, "prepare_%s" % field_name)(obj, language)
                self.prepared_data[field.index_fieldname] = value

        return self.prepared_data
    
    def full_prepare(self, obj, language):
        self.prepared_data = self.prepare(obj, language)

        for field_name, field in self.fields.items():
            # Duplicate data for faceted fields.
            if getattr(field, 'facet_for', None):
                source_field_name = self.fields[field.facet_for].index_fieldname

                # If there's data there, leave it alone. Otherwise, populate it
                # with whatever the related field has.
                if self.prepared_data[field_name] is None and source_field_name in self.prepared_data:
                    self.prepared_data[field.index_fieldname] = self.prepared_data[source_field_name]

            # Remove any fields that lack a value and are ``null=True``.
            if field.null is True:
                if self.prepared_data[field.index_fieldname] is None:
                    del(self.prepared_data[field.index_fieldname])

        return self.prepared_data
    
    def prepare_language(self, obj, language):
        return language.code