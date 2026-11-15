from qfdmd.emoji_lists import make_bullet_paragraphs_lists


def test_consecutive_paragraphs_with_same_marker_become_a_list():
    html = (
        '<p class="fr-card__desc" data-block-key="a">✅ Épluchures.</p>'
        '<p class="fr-card__desc" data-block-key="b">✅ Pain.</p>'
    )

    assert make_bullet_paragraphs_lists(html) == (
        '<ul class="fr-raw-list fr-card__desc">'
        '<li data-block-key="a">✅ Épluchures.</li>'
        '<li data-block-key="b">✅ Pain.</li>'
        "</ul>"
    )


def test_marker_wrapped_in_bold_and_with_variation_selector_is_grouped():
    html = (
        "<p><b>‼️</b> <b>Huiles</b> usagées.</p>\n"
        "<p>‼️ <b>Déchets</b> non alimentaires.</p>"
        "<p><b>‼️ Lombricomposteur</b> : attention.</p>"
    )

    result = make_bullet_paragraphs_lists(html)

    assert result.count("<li") == 3
    assert result.startswith('<ul class="fr-raw-list">')
    assert result.endswith("</ul>")


def test_single_marked_paragraph_is_left_alone():
    html = "<p>👉 Retrouvez la vidéo.</p><p>✅ Un seul.</p>"

    assert make_bullet_paragraphs_lists(html) == html


def test_different_markers_are_not_merged():
    html = "<p>✅ Oui.</p><p>🟠 Peut-être.</p>"

    assert make_bullet_paragraphs_lists(html) == html


def test_paragraph_between_two_runs_splits_them():
    html = "<p>✅ A.</p><p>✅ B.</p><p>Texte.</p><p>✅ C.</p><p>✅ D.</p>"

    result = make_bullet_paragraphs_lists(html)

    assert result.count("<ul") == 2
    assert "<p>Texte.</p>" in result


def test_unmarked_paragraphs_are_untouched():
    html = "<p>Texte</p><p>- Tiret</p>"

    assert make_bullet_paragraphs_lists(html) == html
