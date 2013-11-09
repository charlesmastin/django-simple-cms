from pysolr import SolrError
from haystack.backends.solr_backend import SolrSearchBackend, SolrSearchQuery
from haystack.backends import BaseEngine
from haystack.utils import get_identifier
from simple_cms.contrib.translated_model.models import Language

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