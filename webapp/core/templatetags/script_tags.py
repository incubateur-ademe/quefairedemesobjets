import logging

from django import template
from django.conf import settings
from django.urls import reverse

from assistant.objets import capitalize_first, synonyme_of_term
from qfdmd.models import ProduitPage
from qfdmd.templatetags.qfdmd_tags import get_search_term_name

register = template.Library()

logger = logging.getLogger(__name__)


def searched_synonyme(request, page):
    """The synonyme of `page` the visitor came through, from the search, or None."""
    if request is None:
        return None
    term = get_search_term_name({"request": request})
    return synonyme_of_term(term.pk, page) if term else None


def generate_iframe_script(request, page=None) -> str:
    """Generates a <script> tag used to embed Assistant website.

    Detects the current product page either by Django view name
    (qfdmd:synonyme-detail) or by Wagtail page context (ProduitPage),
    and includes a data-objet attribute with the product slug when applicable.
    `data-synonyme` names the synonyme the visitor searched for: `data-objet`
    keeps the fiche, so a synonyme removed later never breaks the embed.
    """
    script_parts = ["<script"]
    produit_slug = None
    synonyme = None

    if (
        request
        and request.resolver_match
        and request.resolver_match.view_name == "qfdmd:synonyme-detail"
    ):
        produit_slug = request.resolver_match.kwargs.get("slug")
    elif isinstance(page, ProduitPage):
        produit_slug = page.slug
        synonyme = searched_synonyme(request, page)

    if produit_slug:
        script_parts.append(f'data-objet="{produit_slug}"')
    if synonyme:
        script_parts.append(f'data-synonyme="{synonyme.slug}"')

    script_parts.append(f'src="{settings.BASE_URL}{reverse("qfdmd:script")}"></script>')
    return " ".join(script_parts)


@register.simple_tag(takes_context=True)
def assistant_iframe_script(context: dict) -> str:
    if request := context.get("request"):
        return generate_iframe_script(
            request, page=context.get("page") or context.get("self")
        )

    return ""


@register.simple_tag(takes_context=True)
def page_formatted_for_script(context: dict) -> str:
    page = context.get("page", "")
    if page and isinstance(page, ProduitPage):
        if synonyme := searched_synonyme(context.get("request"), page):
            nom = capitalize_first(synonyme.get_title())
            return f"Page “{nom} - {page.title}”"
        return f"Page “{page.title}”"

    return ""


@register.simple_tag(takes_context=True)
def embed_modal_title(context: dict) -> str:
    from core.constants import ASSISTANT

    page = context.get("page", "")
    if page and isinstance(page, ProduitPage):
        return ASSISTANT["embed"]["titre_pages_produit"]

    return ASSISTANT["embed"]["titre_pages"]


@register.simple_tag()
def infotri_script_url() -> str:
    return f"{settings.BASE_URL}{reverse('infotri:infotri_script')}"


@register.simple_tag()
def infotri_configurateur_script_url() -> str:
    return f"{settings.BASE_URL}{reverse('infotri:infotri_configurator_script')}"
