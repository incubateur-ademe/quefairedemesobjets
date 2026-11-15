from django import template
from django.utils.safestring import mark_safe

from qfdmd.emoji_lists import make_bullet_paragraphs_lists

register = template.Library()


class BulletListsNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return mark_safe(make_bullet_paragraphs_lists(self.nodelist.render(context)))


@register.tag
def bullet_lists(parser, token):
    nodelist = parser.parse(("endbullet_lists",))
    parser.delete_first_token()
    return BulletListsNode(nodelist)
