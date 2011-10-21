from django import template
from django.template import Node
from django.contrib.sites.models import Site

register = template.Library()

class SorlNode(template.Node):
    def __init__(self, image, var_name):
        self.image = template.Variable(image)
        self.var_name = var_name
    
    def render(self, context):
        ext = str(self.image.resolve(context)).split('.')[-1].lower()
        if ext == 'png':
            format = 'PNG'
        if ext in ('jpeg', 'jpg', 'gif'):
            format = 'JPEG'
        context[self.var_name] = format
        return ''

@register.tag
def sorl_format(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
        args = arg.split()
    except ValueError:
        raise template.TemplateSyntaxError, 'syntax error'
    return SorlNode(args[0], args[2])

class ExternalNode(template.Node):
    def __init__(self, url, var_name):
        self.url = template.Variable(url)
        self.var_name = var_name
    
    def render(self, context):
        from simple_cms.contrib.utils import is_external_url
        protocol = 'http://'
        if context['request'].is_secure():
            protocol = 'https://'
        context[self.var_name] = is_external_url(
                                    self.url.resolve(context),
                                    '%s%s%s' % (
                                        protocol,
                                        context['request'].get_host(),
                                        context['request'].path
                                    )
                                )
        return ''

@register.tag
def is_external_url(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
        args = arg.split()
    except ValueError:
        raise template.TemplateSyntaxError, 'syntax error'
    return ExternalNode(args[0], args[2])

# http://djangosnippets.org/snippets/660/
class SplitListNode(template.Node):
    def __init__(self, list_string, chunk_size, new_list_name):
        self.list = list_string
        self.chunk_size = chunk_size
        self.new_list_name = new_list_name
    
    def split_seq(self, seq, size):
        """ Split up seq in pieces of size, from
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/425044"""
        return [seq[i:i+size] for i in range(0, len(seq), size)]
    
    def render(self, context):
        context[self.new_list_name] = self.split_seq(context[self.list], int(self.chunk_size))
        return ''

# http://brandonkonkle.com/blog/2010/may/26/snippet-django-columns-filter/
@register.filter
def columns(lst, cols):
    """
    Break a list into ``n`` lists, typically for use in columns.
    
    >>> lst = range(10)
    >>> for list in columns(lst, 3):
    ...     list
    [0, 1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]
    """
    try:
        cols = int(cols)
        lst = list(lst)
    except (ValueError, TypeError):
        raise StopIteration()
    
    start = 0
    for i in xrange(cols):
        stop = start + len(lst[i::cols])
        yield lst[start:stop]
        start = stop

@register.tag
def split_list(parser, token):
    """<% split_list list as new_list 5 %>"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError, "split_list list as new_list 5"
    return SplitListNode(bits[1], bits[4], bits[3])

class PathNode(template.Node):
    def __init__(self, path, depth, variable):
        self.path = template.Variable(path)
        self.depth = template.Variable(depth)
        self.variable = variable
    
    def render(self, context):
        found = False
        depth = self.depth.resolve(context)
        path = self.path.resolve(context)
        url = context['request'].path
        
        if path == url:
            found = True
        
        paths = path.strip('/').split('/')
        urls = url.strip('/').split('/')
        
        matches = 0
        for i in xrange(0, depth):
            try:
                if paths[i] == urls[i]:
                    matches += 1
            except IndexError:
                pass
        if matches == depth:
            found = True
        
        context[self.variable] = found
        return ''

@register.tag
def path_in_url(parser, token):
    try:
        args = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    return PathNode(args[1], args[2], args[4])