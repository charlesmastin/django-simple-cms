from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend, ElasticsearchSearchQuery
from haystack.backends import BaseEngine
from haystack.constants import ID, DJANGO_CT, DJANGO_ID

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

class MultiLanguageElasticsearchEngine(BaseEngine):
    backend = MultiLanguageElasticsearchSearchBackend
    query = ElasticsearchSearchQuery