from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork() -> dict:
    from qfdmd.models import Synonyme

    produits = (
        Synonyme.objects.exclude(picto="")
        .exclude(picto=None)
        .filter(pin_on_homepage=True)
    )
    return {"top": produits[:10], "left": produits[10:14], "right": produits[16:19]}


@register.simple_tag
def render_file_content(svg_file) -> str:
    # Plante si le SVG n'exise pas, ce serat bien que ça ne plante pas car ce n'est pas
    # une fonctionnalité corps de l'application
    with svg_file.open() as f:
        return mark_safe(f.read().decode("utf-8"))
