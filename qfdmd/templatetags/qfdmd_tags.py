import logging
from typing import cast

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

    def get_file_content() -> str:
        # file_field.storage.exists(file_field.name) doesn't work with CleverCloud s3
        # So we use a try except to catch FileNotFoundError error
        try:
            with file_field.storage.open(file_field.name) as f:
                return mark_safe(f.read().decode("utf-8"))  # noqa: S308
        except FileNotFoundError as e:
            logger.error(f"file not found {file_field.name=}, original error : {e}")
            return ""

    return cast(
        str,
        cache.get_or_set(
            f"filefield-{file_field.name}-"
            f"{file_field.size if hasattr(file_field, 'size') else 0}",
            get_file_content,
        ),
    )


@register.inclusion_tag("head/favicon.html")
def favicon() -> dict:
    return {}


@register.inclusion_tag("tracking/matomo.html")
def matomo():
    return {
        "matomo_url": "stats.beta.gouv.fr",
        "matomo_id": settings.ASSISTANT["MATOMO_ID"],
    }
