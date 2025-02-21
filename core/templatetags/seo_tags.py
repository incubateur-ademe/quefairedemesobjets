from urllib.parse import quote, quote_plus

from django import template

from core.constants import SHARE_BODY, SHARE_INTRO

register = template.Library()


def get_sharer_content(request, object, social_network=None):
    """This "dummy" function is defined here to provide
    similar features for jinja and django templating language.
    Once jinja will be removed from the project, this can be merged in
    share_url function below
    """
    try:
        url = quote_plus(object.get_share_url(request))
    except AttributeError:
        url = quote_plus(request.build_absolute_uri())

    template = {
        "url": url,
        "facebook": {
            "title": f"partager {object} sur Facebook - nouvelle fenêtre",
            "url": f"https://www.facebook.com/sharer.php?u={url}",
        },
        "twitter": {
            "title": f"partager {object} sur X - nouvelle fenêtre",
            "url": f"https://twitter.com/intent/tweet?url={url}"
            "&text={SHARE_INTRO}&via=Longue+vie+aux+objets&hashtags=longuevieauxobjets,ademe",
        },
        "linkedin": {
            "title": f"partager {object} sur LinkedIn - nouvelle fenêtre",
            "url": f"https://www.linkedin.com/shareArticle?url={url}&title={SHARE_INTRO}",
        },
        "email": {
            "title": f"partager {object} par email - nouvelle fenêtre",
            "url": f"mailto:?subject={quote(SHARE_INTRO)}"
            f"&body={quote(SHARE_BODY)} {url}",
        },
    }
    if not social_network:
        return template

    return template[social_network]


@register.simple_tag(takes_context=True)
def configure_sharer(context):
    """This template tag enriches the context of a Dechet/Produit/Synonyme.
    Once Jinja will be dropped, it could be merged with the function above."""
    try:
        object = context.get("object").produit
    except AttributeError:
        object = None
    request = context["request"]
    context["sharer"] = get_sharer_content(request, object)
    return ""
