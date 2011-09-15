
from django import template
from django.template import Node

from simple_cms.models import Navigation, Block

register = template.Library()


class NavNode(template.Node):
    def __init__(self, group, var_name):
        self.group = template.Variable(group)
        self.var_name = var_name
    
    def render(self, context):
        # look it up
        nav = Navigation.objects.get_active().filter(group__title=self.group.resolve(context)).order_by('order')
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
            c = Block.objects.get(key=self.key.resolve(context))
            content = c.content
        except Block.DoesNotExist:
            content = ''
        context[self.var_name] = content
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


@register.tag
def split_list(parser, token):
    """<% split_list list as new_list 5 %>"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError, "split_list list as new_list 5"
    return SplitListNode(bits[1], bits[4], bits[3])
    
#split_list = register.tag(split_list)

class PathNode(template.Node):
    def __init__(self, path, variable):
        self.path = template.Variable(path)
        self.variable = variable
    
    def render(self, context):
        found = False
        """
        general search, too weak
        if re.search(self.path.resolve(context), context['request'].path):
            found = True
        match exact leading string
        
        /section/sub/sub/
        /section/sub/
        """
        href = self.path.resolve(context)
        path = context['request'].path
        
        if href == path:
            found = True
        
        if len(path.split('/')) > 3:
            
            if len(href) > len(path):
                if href[0:len(path)] == path:
                    found = True
            else:
                if path[0:len(href)] == href:
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
    return PathNode(args[1], args[3])