from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork():
    from qfdmd.models import Synonyme

    produits = (
        Synonyme.objects.exclude(picto="")
        .exclude(picto=None)
        .filter(pin_on_homepage=True)
    )
    return {"top": produits[:20], "left": produits[20:25], "right": produits[25:30]}


@register.simple_tag
def render_file_content(svg_file):
    with svg_file.open() as f:
        return mark_safe(f.read().decode("utf-8"))
