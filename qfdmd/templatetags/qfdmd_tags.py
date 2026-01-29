import logging
from typing import cast

from django import template
from django.core.cache import cache
from django.forms import FileField
from django.utils.safestring import mark_safe
from wagtail.models import Page
from wagtail.templatetags.wagtailcore_tags import richtext

from qfdmd.models import ReusableContent
from search.models import SearchTerm

register = template.Library()

logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def get_search_term_name(context):
    """
    Retrieve the search term name from the request's search_term_id query parameter.
    """
    request = context.get("request")
    if not request:
        return None

    search_term_id = request.GET.get("search_term_id")
    if not search_term_id:
        return None

    try:
        search_term = SearchTerm.objects.get(id=search_term_id)
        return search_term.term
    except (SearchTerm.DoesNotExist, ValueError):
        return None


@register.filter
def genre_nombre_from(reusable_content: ReusableContent, page):
    """Retrieves reusable content based on page genre and nombre.

    Takes a ReusableContent object and a page (ProduitPage or FamilyPage) and returns
    the appropriate content with placeholder replacement. The content is retrieved based
    on the page's genre and nombre attributes, and any "<objet>" placeholder
    in the content is replaced with the page's titre_phrase or title.
    """
    if not reusable_content:
        return ""

    content = reusable_content.get_from_genre_nombre(page.genre, page.nombre)

    replacement = page.titre_phrase if page.titre_phrase else page.title
    return richtext(content.replace("&lt;objet&gt;", replacement))


@register.inclusion_tag("ui/components/patchwork/patchwork.html")
def patchwork() -> dict:
    from qfdmd.models import Synonyme

    produits = (
        Synonyme.objects.exclude(picto="")
        .exclude(picto=None)
        .filter(pin_on_homepage=True)[:28]
    )
    return {"produits": produits}


@register.inclusion_tag("templatetags/canonical_url.html", takes_context=True)
def canonical_url(context: dict) -> dict:
    if request := context.get("request"):
        return {"url": request.build_absolute_uri(request.path)}


@register.filter
def as_page(page_id):
    if not page_id:
        return ""

    try:
        return Page.objects.get(id=page_id)
    except Page.DoesNotExist:
        return ""


@register.simple_tag
def render_file_content(file_field: FileField) -> str:
    """Renders the content of a Filefield as a safe HTML string
    and caches the result."""

    def get_file_content() -> str:
        # TODO : test this assertion with Scaleway object storage
        # file_field.storage.exists(file_field.name) doesn't work with Scaleway s3
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


@register.inclusion_tag("templatetags/favicon.html")
def favicon() -> dict:
    return {}
