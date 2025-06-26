import logging

from django import template
from django.urls import reverse

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def as_tuple(suggestions) -> list[tuple[str, str]]:
    """
    Converts a list of Suggestion objects into (product name, product URL) tuples.

    Each suggestion must have a `produit` with `nom` and `slug` attributes.
    The URL is generated using the "qfdmd:synonyme-detail" named route.

    :param suggestions: Iterable of Suggestion objects.
    :type suggestions: iterable
    :return: List of (name, URL) tuples.
    """
    return [
        (
            suggestion.produit.nom,
            reverse("qfdmd:synonyme-detail", args=[suggestion.produit.slug]),
        )
        for suggestion in suggestions
    ]
