import pytest

from core.emoji_aria import hide_emojis_from_assistive_tech

VS16 = "\ufe0f"
ZWJ = "\u200d"
KEYCAP = "\u20e3"
HAMMER_AND_WRENCH = "\U0001f6e0" + VS16
RIGHT_ARROW = "➡" + VS16
FAMILY = ZWJ.join(["\U0001f469", "\U0001f469", "\U0001f467", "\U0001f466"])
THUMBS_UP_TONE = "\U0001f44d\U0001f3fd"
FLAG_FR = "\U0001f1eb\U0001f1f7"
ENGLAND_TAGS = "".join(chr(0xE0000 + ord(c)) for c in "gbeng")
FLAG_ENGLAND = "\U0001f3f4" + ENGLAND_TAGS + "\U000e007f"
KEYCAP_ONE = "1" + VS16 + KEYCAP
TRADEMARK_EMOJI = "™" + VS16
CHECK_MARK_BUTTON = "✅"
STAR = "⭐"


SPACE_KEPT = ' style="white-space: pre-wrap"'


def hidden(text: str, style: str = "") -> str:
    return f'<span aria-hidden="true"{style}>{text}</span>'


class TestHideEmojisFromAssistiveTech:
    @pytest.mark.parametrize(
        "emoji",
        [
            CHECK_MARK_BUTTON,
            HAMMER_AND_WRENCH,
            RIGHT_ARROW,
            "⏳",
            THUMBS_UP_TONE,
            FAMILY,
            FLAG_FR,
            FLAG_ENGLAND,
            KEYCAP_ONE,
            TRADEMARK_EMOJI,
            "❤" + VS16,
            "☎" + VS16,
        ],
    )
    def test_wraps_emoji_sequence_as_a_single_unit(self, emoji):
        assert hide_emojis_from_assistive_tech(f"<h2>{emoji}Titre</h2>") == (
            f"<h2>{hidden(emoji)}Titre</h2>"
        )

    def test_includes_the_following_space_in_the_hidden_span(self):
        assert hide_emojis_from_assistive_tech(f"<p>{CHECK_MARK_BUTTON} ok</p>") == (
            f"<p>{hidden(CHECK_MARK_BUTTON + ' ', SPACE_KEPT)}ok</p>"
        )

    def test_wraps_consecutive_emojis_together(self):
        assert hide_emojis_from_assistive_tech("<p>\U0001f4fa\U0001f527 fin</p>") == (
            f"<p>{hidden(chr(0x1F4FA) + chr(0x1F527) + ' ', SPACE_KEPT)}fin</p>"
        )

    @pytest.mark.parametrize(
        "text",
        [
            "© 2026",
            "® marque",
            "™",
            "12 #3 *",
            "Réparer",
            "✓ Réparable",
            "✗ Non",
            "✕",
            "★ ☆",
            "☎ 01 23",
            "☑ fait",
            "❯ suivant",
            "♥ coeur",
            "✔ ok",
            "➡ suite",
        ],
    )
    def test_leaves_text_symbols_and_digits_alone(self, text):
        html = f"<p>{text}</p>"
        assert hide_emojis_from_assistive_tech(html) == html

    @pytest.mark.parametrize("count", [2, 3, 5])
    def test_replaces_stars_with_a_labelled_image(self, count):
        stars = STAR * count
        assert hide_emojis_from_assistive_tech(f"<p>{stars}</p>") == (
            f'<p><span role="img" aria-label="{count} étoiles">{stars}</span></p>'
        )

    @pytest.mark.parametrize("star", [STAR, STAR + VS16])
    def test_hides_a_single_star_like_any_emoji(self, star):
        assert hide_emojis_from_assistive_tech(f"<p>{star}Top</p>") == (
            f"<p>{hidden(star)}Top</p>"
        )

    def test_labels_stars_next_to_other_emojis_separately(self):
        html = hide_emojis_from_assistive_tech(f"<p>{STAR * 2}{CHECK_MARK_BUTTON}</p>")
        assert html == (
            f'<p><span role="img" aria-label="2 étoiles">{STAR * 2}</span>'
            f"{hidden(CHECK_MARK_BUTTON)}</p>"
        )

    @pytest.mark.parametrize(
        "html",
        [
            '<img alt="✅ ok" src="a.png">',
            '<a href="/x" title="\U0001f6e0 outil">lien</a>',
            "<script>const a = '✅'</script>",
            "<style>a::after { content: '✅' }</style>",
            "<textarea>✅ brouillon</textarea>",
            "<head><title>✅ Titre</title></head>",
            "<!-- ✅ commentaire -->",
            '<span aria-hidden="true">✅</span>',
            '<div aria-hidden="true"><p>✅ <b>\U0001f6e0</b></p></div>',
            '<span role="img" aria-label="validé">✅</span>',
            '<span role="img" aria-label="5 étoiles">⭐⭐⭐⭐⭐</span>',
            "<svg><text>✅</text></svg>",
            "<select><option>✅ oui</option></select>",
        ],
    )
    def test_leaves_untouchable_content_alone(self, html):
        assert hide_emojis_from_assistive_tech(html) == html

    def test_resumes_after_hidden_element_closes(self):
        html = '<p><span aria-hidden="true">✅</span> ok \U0001f6e0</p>'
        assert hide_emojis_from_assistive_tech(html) == (
            f'<p><span aria-hidden="true">✅</span> ok {hidden(chr(0x1F6E0))}</p>'
        )

    def test_handles_void_elements_and_attributes_containing_angle_brackets(self):
        html = '<p>a<br>✅ <img alt="x > ✅"> \U0001f6e0</p>'
        assert hide_emojis_from_assistive_tech(html) == (
            f'<p>a<br>{hidden("✅")} <img alt="x > ✅"> {hidden(chr(0x1F6E0))}</p>'
        )

    def test_is_idempotent(self):
        once = hide_emojis_from_assistive_tech(f"<li>{RIGHT_ARROW} Item{STAR}</li>")
        assert hide_emojis_from_assistive_tech(once) == once

    def test_returns_html_without_emoji_unchanged(self):
        html = "<main><p>Bonjour</p></main>"
        assert hide_emojis_from_assistive_tech(html) == html

    def test_keeps_a_single_following_space_only_before_text(self):
        html = f"<p>{CHECK_MARK_BUTTON} <b>x</b></p>"
        assert hide_emojis_from_assistive_tech(html) == (
            f"<p>{hidden(CHECK_MARK_BUTTON)} <b>x</b></p>"
        )


def test_rating_labels_are_configurable():
    html = hide_emojis_from_assistive_tech("<p>⭐⭐</p>", "star", "stars")
    assert 'aria-label="2 stars"' in html
