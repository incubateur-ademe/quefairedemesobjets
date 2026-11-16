from core.templatetags.external_link_tags import announce_new_window


def test_adds_title_to_blank_link_without_mention():
    html = '<p><a href="https://a.fr" target="_blank">Un lien</a></p>'

    assert 'title="Un lien - nouvelle fenêtre"' in announce_new_window(html)


def test_keeps_link_already_mentioning_new_window_in_text():
    html = (
        '<a href="https://a.fr" target="_blank">Un lien'
        '<span class="fr-sr-only">Ouvre une nouvelle fenêtre</span></a>'
    )

    assert "title=" not in announce_new_window(html)


def test_keeps_existing_title_mentioning_new_window():
    html = '<a href="https://a.fr" target="_blank" title="X - nouvelle fenêtre">X</a>'

    assert announce_new_window(html).count("title=") == 1


def test_ignores_links_in_same_tab():
    html = '<a href="/page">Interne</a>'

    assert announce_new_window(html) == html


def test_appends_mention_to_existing_title_without_replacing_it():
    html = '<a href="https://a.fr" target="_blank" title="Détail">Un lien</a>'

    assert 'title="Détail - nouvelle fenêtre"' in announce_new_window(html)


def test_uses_the_given_mention():
    html = '<a href="https://a.fr" target="_blank">Un lien</a>'

    assert 'title="Un lien - new tab"' in announce_new_window(html, "new tab")
