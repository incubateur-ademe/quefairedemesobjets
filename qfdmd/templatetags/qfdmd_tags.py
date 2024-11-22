from django import template

register = template.Library()


@register.inclusion_tag("components/carte/carte.html", takes_context=True)
def carte_from(context, produit):
    request = context["request"]
    try:
        return {
            "carte_settings": produit.sous_categorie_with_carte_display.carte_settings.items(),
            "request": request,
        }
    except AttributeError:
        return {}


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork():
    from qfdmd.models import Produit

    produits = Produit.objects.exclude(picto="").exclude(picto=None)
    items = list(produits) * 8
    return {"top": items[:24], "left": items[20:26], "right": items[24:30]}
