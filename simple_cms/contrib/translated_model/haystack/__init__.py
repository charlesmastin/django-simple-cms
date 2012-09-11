from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.template import loader, Context

from simple_cms.contrib.translated_model.models import Language

from haystack import indexes
from haystack.backends.solr_backend import *
from haystack.utils import get_identifier
from haystack.backends import BaseEngine
from haystack.fields import CharField
from haystack.exceptions import SearchFieldError
from pysolr import SolrError

class MultiLanguageSolrBackend(SolrSearchBackend):
    def update(self, index, iterable, commit=True):
        docs = []

        for language in Language.objects.get_active():
            for obj in iterable:
                try:
                    docs.append(index.full_prepare(obj, language))
                except UnicodeDecodeError:
                    if not self.silently_fail:
                        raise

                    # We'll log the object identifier but won't include the actual object
                    # to avoid the possibility of that generating encoding errors while
                    # processing the log message:
                    self.log.error(u"UnicodeDecodeError while preparing object for update", exc_info=True, extra={
                        "data": {
                            "index": index,
                            "object": '%s.%s' % (get_identifier(obj), language.code)
                        }
                    })

        if len(docs) > 0:
            try:
                self.conn.add(docs, commit=commit, boost=index.get_field_weights())
            except (IOError, SolrError), e:
                if not self.silently_fail:
                    raise

                self.log.error("Failed to add documents to Solr: %s", e)

class MultiLanguageSolrEngine(BaseEngine):
    backend = MultiLanguageSolrBackend
    query = SolrSearchQuery

class MultiLanguageCharField(CharField):
    def _prepare_template(self, obj, language):
        if self.instance_name is None and self.template_name is None:
            raise SearchFieldError("This field requires either its instance_name variable to be populated or an explicit template_name in order to load the correct template.")

        if self.template_name is not None:
            template_names = self.template_name

            if not isinstance(template_names, (list, tuple)):
                template_names = [template_names]
        else:
            template_names = ['search/indexes/%s/%s_%s.txt' % (obj._meta.app_label, obj._meta.module_name, self.instance_name)]
        t = loader.select_template(template_names)
        return t.render(Context({'object': obj, 'language': language}))

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
