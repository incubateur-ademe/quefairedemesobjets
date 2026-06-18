from qfdmd.utils import see_more_button


def test_see_more_button_wraps_url():
    button = see_more_button("https://example.test/fiche/")

    assert button["label"] == "Voir plus de recommandations"
    assert button["extra_classes"] == "fr-btn--icon-left fr-icon-external-link-line"
    assert button["onclick"] == (
        "window.open('https://example.test/fiche/?utm_source=qfdmod'"
        ", '_blank', 'noopener,noreferrer')"
    )
