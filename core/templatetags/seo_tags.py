from urllib.parse import quote, quote_plus

from django import template

register = template.Library()


def get_sharer_content(request, object, social_network=None):
    """This "dummy" function is defined here to provide
    similar features for jinja and django templating language.
    Once jinja will be removed from the project, this can be merged in
    share_url function below"""
    try:
        url = quote_plus(object.get_share_url(request))
    except AttributeError:
        url = quote_plus(request.build_absolute_uri())

    INTRO = "Découvrez le site de l'ADEME “Que faire de mes objets & déchets”"
    BODY = ("Bonjour,\n "
            "Vous souhaitez encourager au tri et la consommation responsable, "
            "le site de l’ADEME “Que faire de mes objets & déchets” accompagne "
            "les citoyens grâce à des bonnes pratiques et adresses près de chez eux,"
            " pour éviter l'achat neuf et réduire les déchets.\n"
            "Découvrez le ici : "
            )

    template = {
        "url": url,
        "facebook": {
            "title": f"partager {object} sur Facebook - nouvelle fenêtre",
            "url": f"https://www.facebook.com/sharer.php?u={url}",
        },
        "twitter": {
            "title": f"partager {object} sur X - nouvelle fenêtre",
            "url": f"https://twitter.com/intent/tweet?url={url}&text={INTRO}&via=Longue+vie+aux+objets&hashtags=longuevieauxobjets,ademe",
        },
        "linkedin": {
            "title": f"partager {object} sur LinkedIn - nouvelle fenêtre",
            "url": f"https://www.linkedin.com/shareArticle?url={url}&title={INTRO}",
        },
        "email": {
            "title": f"partager {object} par email - nouvelle fenêtre",
            "url": f"mailto:?subject={quote(INTRO)}&body={quote(BODY)} {url}"
        },
    }
    if not social_network:
        return template

    return template[social_network]


@register.simple_tag(takes_context=True)
def configure_sharer(context):
    object = context["object"].produit
    request = context["request"]
    context["sharer"] = get_sharer_content(request, object)
    return ""
