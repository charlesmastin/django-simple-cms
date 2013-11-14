from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend, ElasticsearchSearchQuery
from haystack.backends import BaseEngine
from haystack.constants import ID, DJANGO_CT, DJANGO_ID
from haystack.utils import get_identifier

import requests
import pyelasticsearch

from simple_cms.contrib.translated_model.models import Language

class MultiLanguageElasticsearchSearchBackend(ElasticsearchSearchBackend):
    def update(self, index, iterable, commit=True):
        if not self.setup_complete:
            try:
                self.setup()
            except (requests.RequestException, pyelasticsearch.ElasticHttpError) as e:
                if not self.silently_fail:
                    raise

                self.log.error("Failed to add documents to Elasticsearch: %s", e)
                return

        prepped_docs = []

        for language in Language.objects.get_active():
            for obj in iterable:
                try:
                    prepped_data = index.full_prepare(obj, language)
                    final_data = {}

                    # Convert the data to make sure it's happy.
                    for key, value in prepped_data.items():
                        final_data[key] = self._from_python(value)

                    prepped_docs.append(final_data)
                except (requests.RequestException, pyelasticsearch.ElasticHttpError) as e:
                    if not self.silently_fail:
                        raise

                    # We'll log the object identifier but won't include the actual object
                    # to avoid the possibility of that generating encoding errors while
                    # processing the log message:
                    self.log.error(u"%s while preparing object for update" % e.__class__.__name__, exc_info=True, extra={
                        "data": {
                            "index": index,
                            "object": get_identifier(obj)
                        }
                    })
        
        self.conn.bulk_index(self.index_name, 'modelresult', prepped_docs, id_field=ID)

        if commit:
            self.conn.refresh(index=self.index_name)

    def remove(self, obj_or_string, commit=True):
        doc_id = get_identifier(obj_or_string)

        if not self.setup_complete:
            try:
                self.setup()
            except (requests.RequestException, pyelasticsearch.ElasticHttpError) as e:
                if not self.silently_fail:
                    raise

                self.log.error("Failed to remove document '%s' from Elasticsearch: %s", doc_id, e)
                return

        try:
            # iterate over the languages here
            # consider what might happen if we change up the active status or set of languages on demand
            for language in Language.objects.get_active():
                self.conn.delete(self.index_name, 'modelresult', '%s.%s' % (doc_id, language.code))
            
            if commit:
                self.conn.refresh(index=self.index_name)

        except (requests.RequestException, pyelasticsearch.ElasticHttpError) as e:
            if not self.silently_fail:
                raise

            self.log.error("Failed to remove document '%s' from Elasticsearch: %s", doc_id, e)

class MultiLanguageElasticsearchEngine(BaseEngine):
    backend = MultiLanguageElasticsearchSearchBackend
    query = ElasticsearchSearchQuery

def multilanguage_do_remove(backend, index, model, pks_seen, start, upper_bound, verbosity=1):
    # Fetch a list of results.
    # Can't do pk range, because id's are strings (thanks comments
    # & UUIDs!).
    stuff_in_the_index = SearchQuerySet().models(model)[start:upper_bound]
    # Do some hack things for the languages
    ids = set()
    items = []
    for item in stuff_in_the_index:
        # are we in the temp
        if not item.pk in ids:
            items.append(item)
        ids.add(item.pk)

    # Iterate over those results.
    for result in items:
        # Be careful not to hit the DB.
        if not smart_bytes(result.pk) in pks_seen:
            # The id is NOT in the small_cache_qs, issue a delete.
            if verbosity >= 2:
                print("  removing %s." % result.pk)

            backend.remove(".".join([result.app_label, result.model_name, str(result.pk)]))
