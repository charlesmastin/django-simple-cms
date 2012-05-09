from django.views.generic import ListView
from simple_cms.contrib.utils import digg_paginator

class DataGridView(ListView):
    sort_column = None
    sort_direction = 'asc'
    sort = None
    querystring = None
    headers = []
    digg = True
    
    def get(self, request, *args, **kwargs):
        self.querystring = request.GET.copy()
        querystring = request.GET.copy()
        try:
            del(self.querystring['page'])
            del(querystring['page'])
        except KeyError:
            pass
        try:
            self.sort = request.GET['sort_column']
            self.sort_column = self.sort
            self.sort_direction = request.GET['sort_direction']
            if request.GET['sort_direction'] == 'desc':
                self.sort = '-%s' % self.sort
        except:
            self.sort = self.sort_column
            if self.sort_direction == 'desc':
                self.sort = '-%s' % self.sort
        for header in self.headers:
            try:
                querystring['sort_column'] = header['column']
                querystring['sort_direction'] = 'asc'
                if header['column'] == self.sort_column:
                    header['class'] = 'active'
                    if self.sort_direction == 'desc':
                        header['class'] = '%s asc' % header['class']
                        querystring['sort_direction'] = 'asc'
                    if self.sort_direction == 'asc':
                        header['class'] = '%s desc' % header['class']
                        querystring['sort_direction'] = 'desc'
                else:
                    header['class'] = ''
                    pass
                header['href'] = querystring.urlencode()
            except KeyError:
                pass
        return super(DataGridView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super(DataGridView, self).get_queryset()
        return queryset.order_by(self.sort)
    
    def get_context_data(self, *args, **kwargs):
        context = super(DataGridView, self).get_context_data(*args, **kwargs)
        context['headers'] = self.headers
        context['querystring'] = self.querystring.urlencode()
        if self.digg:
            context['digg'] = digg_paginator(context['page_obj'])
        return context

