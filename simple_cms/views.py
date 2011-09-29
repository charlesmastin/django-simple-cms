from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.conf import settings
from django.views.generic import ListView, DateDetailView
from django.db.models import Q

from simple_cms.models import Navigation, Article
from simple_cms.forms import ArticleSearchForm


def page(request, template=''):
    if template == '':
        template = settings.SIMPLE_CMS_PAGE_TEMPLATE
    context = RequestContext(request)
    for i in context['pageA']:
        if i.template:
            template = i.template
    if context['page'].view:
        # dynamic import, not a terrible risk
        tA = context['page'].view.split('.')
        c = tA.pop()
        import_string = 'from %s import %s' % ('.'.join(tA), c)
        exec import_string
        return eval(c)(request=request)
    return render_to_response(
        template,
        { },
        context_instance=RequestContext(request)
    )


class ArticleListView(ListView):

    def get_context_data(self, *kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        context['article_search_form'] = ArticleSearchForm()


class ArticleDetailView(DateDetailView):

    def get_context_data(self, *kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        context['article_search_form'] = ArticleSearchForm()


class ArticleTagView(ListView):

    def get(self, request, *args, **kwargs):
        self.tag = kwargs['slug']
        return super(ArticleTagView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        return Article.objects.get_active().filter(tags__slug__in=[self.tag])


class ArticleSearchView(ListView):

    def get(self, request, *args, **kwargs):
        self.form = ArticleSearchForm(request.GET or None)
        return super(ArticleSearchView, self).get(self, request, *args, **kwargs)

    def get_queryset(self):
        articles = None
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
        context['article_search_form'] = self.form
        return context