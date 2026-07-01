UTM_SOURCE = "qfdmod"


def see_more_button(url: str) -> dict[str, str]:
    """Build the "Voir plus de recommandations" footer button shown in the iframe.

    The button opens the standalone version of the fiche in a new tab. It is
    used both by ProduitPage (Wagtail) and SynonymeDetailView (legacy fiche),
    which is why it lives here rather than being duplicated in each.

    The standalone URL is tagged with ``utm_source`` so visits coming from the
    iframe footer are attributable. Callers always pass an untagged URL.
    """
    tagged_url = f"{url}?utm_source={UTM_SOURCE}"
    return {
        "label": "Voir plus de recommandations",
        "extra_classes": "fr-btn--icon-left fr-icon-external-link-line",
        "onclick": f"window.open('{tagged_url}', '_blank', 'noopener,noreferrer')",
    }
