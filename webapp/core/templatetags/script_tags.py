import logging

from django import template
from django.conf import settings
from django.urls import reverse

from qfdmd.models import ProduitPage

register = template.Library()

logger = logging.getLogger(__name__)


def generate_iframe_script(request, page=None) -> str:
    """Generates a <script> tag used to embed Assistant website.

    Detects the current product page either by Django view name
    (qfdmd:synonyme-detail) or by Wagtail page context (ProduitPage),
    and includes a data-objet attribute with the product slug when applicable.
    """
    script_parts = ["<script"]
    produit_slug = None

    if (
        request
        and request.resolver_match
        and request.resolver_match.view_name == "qfdmd:synonyme-detail"
    ):
        produit_slug = request.resolver_match.kwargs.get("slug")
    elif isinstance(page, ProduitPage):
        produit_slug = page.slug

    if produit_slug:
        script_parts.append(f'data-objet="{produit_slug}"')

    script_parts.append(f'src="{settings.BASE_URL}{reverse("qfdmd:script")}"></script>')
    return " ".join(script_parts)


@register.simple_tag(takes_context=True)
def assistant_iframe_script(context: dict) -> str:
    if request := context.get("request"):
        return generate_iframe_script(
            request, page=context.get("page") or context.get("self")
        )

    return ""


@register.simple_tag()
def infotri_script_url() -> str:
    return f"{settings.BASE_URL}{reverse('infotri:infotri_script')}"


@register.simple_tag()
def infotri_configurateur_script_url() -> str:
    return f"{settings.BASE_URL}{reverse('infotri:infotri_configurator_script')}"
