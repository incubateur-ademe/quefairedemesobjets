from qfdmd.utils import lire_plus_button


def test_lire_plus_button_wraps_url():
    button = lire_plus_button("https://example.test/fiche/")

    assert button["label"] == "Lire plus sur cette fiche"
    assert button["extra_classes"] == "fr-btn--icon-left fr-icon-external-link-line"
    assert button["onclick"] == (
        "window.open('https://example.test/fiche/?utm_source=qfdmod'"
        ", '_blank', 'noopener,noreferrer')"
    )
