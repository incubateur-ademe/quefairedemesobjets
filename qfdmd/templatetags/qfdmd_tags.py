from django import template
from django.conf import settings
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
    with svg_file.open() as f:
        return mark_safe(f.read().decode("utf-8"))


@register.inclusion_tag("head/favicon.html")
def favicon() -> dict:
    return {}


@register.inclusion_tag("tracking/matomo.html")
def matomo():
    return {
        "matomo_url": "stats.beta.gouv.fr",
        "matomo_id": settings.ASSISTANT["MATOMO_ID"],
    }


@register.inclusion_tag("tracking/posthog.html")
def posthog():
    return {"posthog_key": settings.ASSISTANT["POSTHOG_KEY"]}
