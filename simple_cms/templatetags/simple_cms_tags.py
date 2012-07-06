from django import template
from django.template import Node
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from simple_cms.models import Navigation, Block, Article
from simple_cms.forms import ArticleSearchForm

register = template.Library()

@register.simple_tag(takes_context=True)
def page_url(context, id):
    try:
        nav = Navigation.objects.get(pk=id)
        if nav.url:
            return nav.url
        protocol = 'http://'
        if context['request'].is_secure():
            protocol = 'https://'
        return '%s%s%s' % (protocol, nav.site.domain, nav.get_absolute_url())
    except Navigation.DoesNotExist:
        return ''

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




class NavigationBlocksNode(template.Node):
    
    def __init__(self, instance, var_name, group_name=''):
        self.instance = template.Variable(instance)
        self.var_name = var_name
        self.group_name = None
        if group_name != '':
            self.group_name = template.Variable(group_name)
    
    def render(self, context):
        blocks = None
        instance = self.instance.resolve(context)
        # spin this off into a separate template tag perhaps
        # we could just filter it all out afterwards, but heck, do 2 optimized queries
        # dynamic args, yo, easy peazy
        # navigation_type = ContentType.objects.get_for_model(Navigation)
        
        try:
            if self.group_name:
                group = self.group_name.resolve(context)
                blocks = [block.block for block in instance.blocks.filter(active=True, group__title=group)]
                if hasattr(instance, 'parent') and hasattr(instance, 'inherit_blocks'):
                    if instance.inherit_blocks:
                        while instance.parent:
                            instance = instance.parent
                            for block in instance.blocks.filter(active=True, group__title=group):
                                blocks.append(block.block)
                            if not instance.inherit_blocks:
                                break
            
            else:
                blocks = [block.block for block in instance.blocks.filter(active=True)]
                if hasattr(instance, 'parent') and hasattr(instance, 'inherit_blocks'):
                    if instance.inherit_blocks:
                        while instance.parent:
                            instance = instance.parent
                            for block in instance.blocks.filter(active=True):
                                blocks.append(block.block)
                            if not instance.inherit_blocks:
                                break
        except:
            pass
        context[self.var_name] = blocks
        return ''


@register.tag
def get_blocks(parser, token):
    """
    Tag should be called like so:
        {% get_blocks for <model instance> [<group string>] as <variable> %}
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

def get_articles(articles, length):
    count = len(articles)
    if length:
        count = articles.count()
        articles = articles[:length]
    return {
        'count': count,
        'objects': articles,
    }

@register.assignment_tag
def get_articles_for_tag(tag, length=None):
    articles = Article.objects.get_active().filter(tags__slug__in=[tag])
    return get_articles(articles, length)

@register.assignment_tag
def get_articles_for_category(category, length=None):
    articles = Article.objects.get_active().filter(category__slug__in=[category])
    return get_articles(articles, length)

