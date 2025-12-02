from urllib.parse import quote, quote_plus

from django import template

from core.constants import ASSISTANT, CARTE

register = template.Library()


def get_sharer_content(request, object, social_network=None):
    """This "dummy" function is defined here to provide
    similar features for jinja and django templating language.
    As jinja does not support the takes_context approach of template.
    Once jinja will be removed from the project, this can be merged in
    share_url function below
    """
    if not request or not request.resolver_match:
        return {}
    carte = request.resolver_match.view_name in ["qfdmo:carte", "qfdmo:carte_custom"]

    url = request.build_absolute_uri()

    share_body = ""
    share_intro = ""
    quoted_url = quote_plus(url)
    format_template = {
        "URL": url,
    }

    if carte:
        share_intro = CARTE["partage"]["titre"]
        share_body = CARTE["partage"]["corps"]
        format_template["NOM"] = object.libelle
    else:
        share_intro = ASSISTANT["partage"]["titre"]
        share_body = ASSISTANT["partage"]["corps"]

    share_intro = share_intro.format(**format_template)
    share_body = share_body.format(**format_template)

    template = {
        "url": url,
        "facebook": {
            "title": f"partager {object} sur Facebook - nouvelle fenêtre",
            "url": f"https://www.facebook.com/sharer.php?u={quoted_url}",
        },
        "twitter": {
            "title": f"partager {object} sur X - nouvelle fenêtre",
            "url": f"https://twitter.com/intent/tweet?url={quoted_url}"
            f"&text={share_intro}&via=Longue+vie+aux+objets&hashtags=longuevieauxobjets,ademe",
        },
        "linkedin": {
            "title": f"partager {object} sur LinkedIn - nouvelle fenêtre",
            "url": f"https://www.linkedin.com/shareArticle?url={quoted_url}&title={share_intro}",
        },
        "email": {
            "title": f"partager {object} par email - nouvelle fenêtre",
            "url": f"mailto:?subject={quote(share_intro)}&body={quote(share_body)}",
        },
    }
    if not social_network:
        return template

    return template[social_network]


def _configure_sharer(context):
    shared_object = context.get("object", "")
    request = context.get("request")
    context["sharer"] = get_sharer_content(request, shared_object)
    return ""


@register.simple_tag(takes_context=True)
def configure_acteur_sharer(context):
    return _configure_sharer(context)


@register.simple_tag(takes_context=True)
def configure_produit_sharer(context):
    return _configure_sharer(context)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def tojson(value):
    """Django filter to replace Jinja2's |tojson filter"""
    import json

    return json.dumps(value)


@register.simple_tag
def random_range(max_value):
    """Generate a random number for cache busting"""
    import random

    return random.randint(0, max_value - 1)
