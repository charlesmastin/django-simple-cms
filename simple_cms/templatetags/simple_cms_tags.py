from django import template
from django.template import Node
from django.contrib.sites.models import Site

from simple_cms.models import Navigation, Block
from simple_cms.forms import ArticleSearchForm

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
        from simple_cms.utils import is_external_url
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


class NavNode(template.Node):
    def __init__(self, group, var_name):
        self.group = template.Variable(group)
        self.var_name = var_name
    
    def render(self, context):
        nav = Navigation.objects.get_active().filter(site=Site.objects.get_current(), group__title=self.group.resolve(context)).order_by('order')
        context[self.var_name] = nav
        return ''


@register.tag
def get_nav_by_group(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
        args = arg.split()
    except ValueError:
        raise template.TemplateSyntaxError, 'syntax error'
    #m = re.search(r'(.*?) as (\w+)', arg)
    return NavNode(args[0], args[2])


class BlockNode(template.Node):
    def __init__(self, key, var_name):
        self.key = template.Variable(key)
        self.var_name = var_name
    
    def render(self, context):
        try:
            block = Block.objects.get(key=self.key.resolve(context))
        except Block.DoesNotExist:
            block = None
        context[self.var_name] = block
        return ''


@register.tag
def get_block(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % \
                token.contents.split()[0]
    bits = arg.split()
    return BlockNode(bits[0], bits[2])


@register.filter
def render_as_template(value, request):
    t = template.Template(value)
    c = template.Context(template.RequestContext(request))
    return t.render(c)


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
    
#split_list = register.tag(split_list)

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
        raise template.TemplateSyntaxError, "%r tag requires arguments" % \
                token.contents.split()[0]
    return PathNode(args[1], args[2], args[4])


class NavigationBlocksNode(template.Node):
    
    def __init__(self, nav_item, var_name, group_name=''):
        self.nav_item = template.Variable(nav_item)
        self.var_name = var_name
        self.group_name = None
        if group_name != '':
            self.group_name = template.Variable(group_name)
    
    def render(self, context):
        blocks = None
        nav = self.nav_item.resolve(context)
        # spin this off into a separate template tag perhaps
        # we could just filter it all out afterwards, but heck, do 2 optimized queries
        # dynamic args, yo, easy peazy
        try:
            if self.group_name:
                group = self.group_name.resolve(context)
                blocks = [block.block for block in nav.navigationblocks_set.filter(active=True, group__title=group)]
                if nav.inherit_blocks:
                    while nav.parent:
                        nav = nav.parent
                        for block in nav.navigationblocks_set.filter(active=True, group__title=group):
                            blocks.append(block.block)
                        if not nav.inherit_blocks:
                            break
            
            else:
                blocks = [block.block for block in nav.navigationblocks_set.filter(active=True)]
                if nav.inherit_blocks:
                    while nav.parent:
                        nav = nav.parent
                        for block in nav.navigationblocks_set.filter(active=True):
                            blocks.append(block.block)
                        if not nav.inherit_blocks:
                            break
        except:
            pass
        context[self.var_name] = blocks
        return ''


@register.tag
def get_blocks(parser, token):
    """
    Tag should be called like so:
        {% get_blocks for <nav object> [<group string>] as <variable> %}
    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % \
                token.contents.split()[0]
    bits = arg.split()
    len_bits = len(bits)
    if len_bits == 5:
        return NavigationBlocksNode(bits[1], bits[4], bits[2])
    if len_bits == 4:
        return NavigationBlocksNode(bits[1], bits[3])
    
    raise TemplateSyntaxError, "get_blocks for nav [group] as varname"
    

class ArticleSearchFormNode(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name
    
    def render(self, context):
        context[self.var_name] = ArticleSearchForm()
        return ''


@register.tag
def get_article_search_form(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % \
                token.contents.split()[0]
    bits = arg.split()
    return ArticleSearchFormNode(bits[1])