from typing import cast
import logging

from django import template
from django.conf import settings
from django.core.cache import cache
from django.forms import FileField
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)


@register.inclusion_tag("components/patchwork/patchwork.html")
def patchwork() -> dict:
    from qfdmd.models import Synonyme

    produits = (
        Synonyme.objects.exclude(picto="")
        .exclude(picto=None)
        .filter(pin_on_homepage=True)[:19]
    )
    return {"top": produits[:10], "left": produits[10:14], "right": produits[16:19]}


@register.simple_tag
def render_file_content(file_field: FileField) -> str:
    """Renders the content of a Filefield as a safe HTML string
    and caches the result."""

    try:

        def get_file_content() -> str:
            with file_field.open() as f:
                return mark_safe(f.read().decode("utf-8"))  # noqa: S308

        return cast(
            str,
            cache.get_or_set(
                f"filefield-{file_field.name}-{file_field.size}", get_file_content
            ),
        )
    except FileNotFoundError as exception:
        # We silent the error here to prevent crashing a page for a missing svg
        logger.warning("An error was quietly ignored")
        logger.error(exception)

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
