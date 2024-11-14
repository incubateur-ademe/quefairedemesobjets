from django import template

register = template.Library()


@register.inclusion_tag("components/carte/carte.html")
def carte_from(produit):
    try:
        return {
            "carte_settings": produit.sous_categorie_with_carte_display.carte_settings.items()
        }
    except AttributeError:
        return {}
