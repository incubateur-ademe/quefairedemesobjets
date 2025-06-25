import logging

from django import template
from django.urls import reverse

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def as_tuple(suggestions):
    return [
        (
            suggestion.produit.nom,
            reverse("qfdmd:synonyme-detail", args=[suggestion.produit.slug]),
        )
        for suggestion in suggestions
    ]
