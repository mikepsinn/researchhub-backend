from elasticsearch_dsl.query import Match
from elasticsearch_dsl import Q
from rest_framework import filters

from .utils import practical_score, get_avgdl
from paper.models import Paper


class ElasticsearchFuzzyFilter(filters.SearchFilter):

    def filter_queryset(self, request, queryset, view):
        search = getattr(view, 'search')
        fields = getattr(view, 'search_fields')
        terms = ' '.join(self.get_search_terms(request))
        query = Q(
            'multi_match',
            query=terms,
            fields=fields,
            fuzziness='AUTO'
        )
        es = search.query(query)
        response = es.execute()
        return response


class ElasticsearchPaperTitleFilter(filters.SearchFilter):

    def filter_queryset(self, request, queryset, view):
        search = getattr(view, 'search')

        search_terms = self.get_search_terms(request)
        terms_count = len(search_terms)
        terms = ' '.join(search_terms)
        query = Match(
            title=terms
        )

        es = search.query(query)
        N = Paper.objects.count()
        dl = len(search_terms)
        avgdl = get_avgdl(es, Paper.objects)
        threshold = practical_score(search_terms, N, dl, avgdl) - terms_count
        response = es.execute()
        response = [res for res in response if res.meta.score >= threshold]
        return response
