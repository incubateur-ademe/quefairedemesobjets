import logging

from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()

logger = logging.getLogger(__name__)


def generate_iframe_script(request) -> str:
    """Generates a <script> tag used to embed Assistant website."""
    script_parts = ["<script"]
    if (
        request
        and request.resolver_match
        and request.resolver_match.view_name == "qfdmd:synonyme-detail"
    ):
        produit_slug = request.resolver_match.kwargs["slug"]
        script_parts.append(f'data-objet="{produit_slug}"')

    script_parts.append(f'src="{settings.BASE_URL}{reverse("qfdmd:script")}"></script>')
    return " ".join(script_parts)


@register.simple_tag(takes_context=True)
def assistant_iframe_script(context: dict) -> str:
    if request := context.get("request"):
        return generate_iframe_script(request)

    return ""
