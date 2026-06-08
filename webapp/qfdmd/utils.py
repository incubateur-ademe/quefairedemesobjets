def lire_plus_button(url: str) -> dict[str, str]:
    """Build the "Lire plus sur cette fiche" footer button shown in the iframe.

    The button opens the standalone version of the fiche in a new tab. It is
    used both by ProduitPage (Wagtail) and SynonymeDetailView (legacy fiche),
    which is why it lives here rather than being duplicated in each.
    """
    return {
        "label": "Lire plus sur cette fiche",
        "extra_classes": "fr-btn--icon-left fr-icon-external-link-line",
        "onclick": f"window.open('{url}', '_blank', 'noopener,noreferrer')",
    }
