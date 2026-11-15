import pytest

from core.emoji_aria import hide_emojis_from_assistive_tech


def wrapped(text: str) -> str:
    return f'<span aria-hidden="true">{text}</span>'


class TestHideEmojisFromAssistiveTech:
    @pytest.mark.parametrize(
        "emoji",
        [
            "✅",
            "🛠️",
            "➡️",
            "⏳",
            "👍🏽",
            "👩‍👩‍👧‍👦",
            "🇫🇷",
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
            "1️⃣",
            "™️",
        ],
    )
    def test_wraps_emoji_sequence_as_a_single_unit(self, emoji):
        assert hide_emojis_from_assistive_tech(f"<h2>{emoji} Titre</h2>") == (
            f"<h2>{wrapped(emoji)} Titre</h2>"
        )

    def test_wraps_consecutive_emojis_together(self):
        assert hide_emojis_from_assistive_tech("<p>📺🔧 fin</p>") == (
            f"<p>{wrapped('📺🔧')} fin</p>"
        )

    @pytest.mark.parametrize("text", ["© 2026", "® marque", "™", "12 #3 *", "Réparer"])
    def test_leaves_text_symbols_and_digits_alone(self, text):
        html = f"<p>{text}</p>"
        assert hide_emojis_from_assistive_tech(html) == html

    @pytest.mark.parametrize(
        "html",
        [
            '<img alt="✅ ok" src="a.png">',
            '<a href="/x" title="🛠️ outil">lien</a>',
            "<script>const a = '✅'</script>",
            "<style>a::after { content: '✅' }</style>",
            "<textarea>✅ brouillon</textarea>",
            "<head><title>✅ Titre</title></head>",
            "<!-- ✅ commentaire -->",
            '<span aria-hidden="true">✅</span>',
            '<div aria-hidden="true"><p>✅ <b>🛠️</b></p></div>',
            '<span role="img" aria-label="validé">✅</span>',
            "<svg><text>✅</text></svg>",
            "<select><option>✅ oui</option></select>",
        ],
    )
    def test_leaves_untouchable_content_alone(self, html):
        assert hide_emojis_from_assistive_tech(html) == html

    def test_resumes_after_hidden_element_closes(self):
        html = '<p><span aria-hidden="true">✅</span> ok 🛠️</p>'
        assert hide_emojis_from_assistive_tech(html) == (
            f'<p><span aria-hidden="true">✅</span> ok {wrapped("🛠️")}</p>'
        )

    def test_handles_void_elements_and_attributes_containing_angle_brackets(self):
        html = '<p>a<br>✅ <img alt="x > ✅"> 🛠️</p>'
        assert hide_emojis_from_assistive_tech(html) == (
            f'<p>a<br>{wrapped("✅")} <img alt="x > ✅"> {wrapped("🛠️")}</p>'
        )

    def test_is_idempotent(self):
        once = hide_emojis_from_assistive_tech("<li>➡️ Item</li>")
        assert hide_emojis_from_assistive_tech(once) == once

    def test_returns_html_without_emoji_unchanged(self):
        html = "<main><p>Bonjour</p></main>"
        assert hide_emojis_from_assistive_tech(html) == html
