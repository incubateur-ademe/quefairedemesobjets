import logging
from typing import cast

from django import template
from django.conf import settings
from django.core.cache import cache
from django.forms import FileField
from django.utils.safestring import mark_safe
from wagtail.templatetags.wagtailcore_tags import richtext

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def richtext_with_objet(reusable_content, page):
    """
    TODO: docstring
    """
    return richtext(reusable_content)
    # .replace("<objet>", page.title))


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork() -> dict:
    from qfdmd.models import Synonyme

    produits = (
        Synonyme.objects.exclude(picto="")
        .exclude(picto=None)
        .filter(pin_on_homepage=True)[:19]
    )
    return {"top": produits[:10], "left": produits[10:14], "right": produits[16:19]}


@register.inclusion_tag("seo/_canonical_url.html", takes_context=True)
def canonical_url(context: dict) -> dict:
    canonical_url = None

    if request := context.get("request"):
        request = context["request"]
        path = request.build_absolute_uri(request.path)
        canonical_url = path.replace(request.get_host(), settings.CANONICAL_HOST)

    return {"canonical_url": canonical_url}


@register.simple_tag
def render_file_content(file_field: FileField) -> str:
    """Renders the content of a Filefield as a safe HTML string
    and caches the result."""

    def get_file_content() -> str:
        # file_field.storage.exists(file_field.name) doesn't work with CleverCloud s3
        # So we use a try except to catch FileNotFoundError error
        with file_field.storage.open(file_field.name) as f:
            return mark_safe(f.read().decode("utf-8"))  # noqa: S308

    try:
        return cast(
            str,
            cache.get_or_set(
                f"filefield-{file_field.name}-"
                f"{file_field.size if hasattr(file_field, 'size') else 0}",
                get_file_content,
            ),
        )
    except FileNotFoundError as e:
        logger.error(f"file not found {file_field.name=}, original error : {e}")
        return ""


@register.inclusion_tag("head/favicon.html")
def favicon() -> dict:
    return {}


@register.inclusion_tag("tracking/matomo.html")
def matomo():
    return {
        "matomo_url": "stats.beta.gouv.fr",
        "matomo_id": settings.ASSISTANT["MATOMO_ID"],
    }
