from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("components/carte/carte.html", takes_context=True)
def carte_from(context, produit):
    request = context["request"]
    try:
        return {
            "carte_settings": produit.sous_categorie_with_carte_display.carte_settings.items(),  # noqa: E501
            "request": request,
        }
    except AttributeError:
        return {}


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork():
    from qfdmd.models import Synonyme

    produits = Synonyme.objects.exclude(picto="").exclude(picto=None)
    return {"top": produits[:24], "left": produits[24:30], "right": produits[30:36]}


@register.simple_tag
def render_file_content(svg_file):
    with svg_file.open() as f:
        return mark_safe(f.read().decode("utf-8"))
