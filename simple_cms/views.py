from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.conf import settings
from django.views.generic import View, ListView, DateDetailView
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseNotFound, Http404
from django.core.urlresolvers import get_callable

from simple_cms.models import Navigation, Article
from simple_cms.forms import ArticleSearchForm


class NavigationView(View):
    template_name = settings.SIMPLE_CMS_PAGE_TEMPLATE

    def post(self, request, *args, **kwargs):
        return self._handler(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._handler(request, *args, **kwargs)

    def _handler(self, request, *args, **kwargs):
        context = RequestContext(request, {})
        if context['page'] and context['exact_match']:
            if context['page'].redirect_url:
                if context['page'].redirect_permanent:
                    return HttpResponsePermanentRedirect(context['page'].redirect_url)
                else:
                    return HttpResponseRedirect(context['page'].redirect_url)
            if context['page'].view:
                if context['page'].view.find('.as_view(') != -1:
                    pass
                else:
                    cls = get_callable(context['page'].view)
                    return cls(request)
            if context['page'].template:
                self.template_name = context['page'].template
            elif context['page'].inherit_template:
                for i in context['pageA']:
                    if i.template:
                        self.template_name = i.template
            return render(request, self.template_name, {}, context_instance=context)
        raise Http404

class ArticleListView(ListView):

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        context['article_search_form'] = ArticleSearchForm()
        return context

class ArticleDetailView(DateDetailView):
    fetch_sequence = True

    def get_context_data(self, **kwargs):
        context = super(ArticleDetailView, self).get_context_data(**kwargs)
        #context['article_search_form'] = ArticleSearchForm()
        if len(self.object.seo.all()) == 1:
            context.update({'seo': self.object.seo.all()[0]})
        if self.fetch_sequence:
            # grab sequence of id, then find
            ids = Article.objects.get_active().values_list('id', flat=True)
            # generator?
            for i, _id in enumerate(ids):
                if self.object.pk == _id:
                    try:
                        context.update({'previous_article': Article.objects.get(pk=ids[i+1])})
                    except:
                        pass
                    try:
                        context.update({'next_article': Article.objects.get(pk=ids[i-1])})
                    except:
                        pass
                    break
        return context

class ArticleTagView(ListView):

    def get(self, request, *args, **kwargs):
        self.tag = kwargs['slug']
        return super(ArticleTagView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        return Article.objects.get_active().filter(tags__slug__in=[self.tag])

    def get_context_data(self, **kwargs):
        context = super(ArticleTagView, self).get_context_data(**kwargs)
        context.update({'tag': self.tag})
        return context

class ArticleCategoryView(ListView):

    def get(self, request, *args, **kwargs):
        self.category = kwargs['slug']
        return super(ArticleCategoryView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        return Article.objects.get_active().filter(categories__slug__in=[self.category])

    def get_context_data(self, **kwargs):
        context = super(ArticleCategoryView, self).get_context_data(**kwargs)
        context.update({'category': self.category})
        return context

class ArticleSearchView(ListView):

    def get(self, request, *args, **kwargs):
        self.form = ArticleSearchForm(request.GET or None)
        return super(ArticleSearchView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        articles = []
        if self.form.is_valid():
            keywords = self.form.cleaned_data['q']
            articles = Article.objects.get_active()
            articles = articles.filter(
                Q(title__icontains=keywords) |
                Q(text__icontains=keywords) |
                Q(excerpt__icontains=keywords) |
                Q(tags__name__in=[keywords])).distinct()
        return articles

    def get_context_data(self, **kwargs):
        context = super(ArticleSearchView, self).get_context_data(**kwargs)
        context['query'] = self.form.cleaned_data['q']
        context['article_search_form'] = self.form
        return context

class ArticleYearView(ListView):

    def get(self, request, *args, **kwargs):
        self.year = kwargs['year']
        return super(ArticleYearView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        return Article.objects.get_active().filter(post_date__year=self.year)

    def get_context_data(self, **kwargs):
        context = super(ArticleYearView, self).get_context_data(**kwargs)
        context.update({'year': self.year})
        return context