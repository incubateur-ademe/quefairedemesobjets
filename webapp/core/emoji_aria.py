import re

SKIPPED_TAGS = frozenset(
    {"head", "title", "script", "style", "textarea", "option", "svg", "math"}
)
RAW_TEXT_TAGS = frozenset({"script", "style", "textarea", "title"})
VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)

_VARIATION_SELECTOR = "️"
_SKIN_TONES = "\U0001f3fb-\U0001f3ff"
# Symbols that render as an emoji on their own.
_EMOJI_BASE = "⌚⌛⏩-⏬⏰⏳◽◾☀-➿⭐⭕" "\U0001f000-\U0001faff"
# Symbols that render as plain text unless followed by U+FE0F (©, ®, ™, arrows…).
_TEXT_DEFAULT_BASE = "©®‼⁉™ℹ↔-↙↩↪Ⓜ▪▫" "▶◀◻◼⌨⏏⏭-⏯⏱⏲⏸-⏺" "⤴⤵⬅-⬇⬛⬜〰〽㊗㊙"
_SINGLE_EMOJI = (
    f"(?:[{_EMOJI_BASE}]{_VARIATION_SELECTOR}?|"
    f"[{_TEXT_DEFAULT_BASE}]{_VARIATION_SELECTOR})[{_SKIN_TONES}]?"
)
_EMOJI_SEQUENCE = f"{_SINGLE_EMOJI}(?:‍{_SINGLE_EMOJI})*"
_FLAG = "[\U0001f1e6-\U0001f1ff]{2}"
_TAG_FLAG = "\U0001f3f4[\U000e0020-\U000e007e]+\U000e007f"
_KEYCAP = f"[0-9#*]{_VARIATION_SELECTOR}?⃣"

EMOJI_RE = re.compile(f"(?:{_TAG_FLAG}|{_KEYCAP}|{_FLAG}|{_EMOJI_SEQUENCE})+")

_TOKEN_RE = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<![^>]*>|<\?.*?\?>"
    r"|<(?P<closing>/?)(?P<name>[a-zA-Z][^\s/>]*)(?P<attrs>(?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>",
    re.DOTALL,
)
_ARIA_HIDDEN_RE = re.compile(r"""\saria-hidden\s*=\s*["']?true["']?""", re.I)
_ROLE_IMG_RE = re.compile(r"""\srole\s*=\s*["']?img["']?""", re.I)

WRAPPER = '<span aria-hidden="true">{}</span>'


def _wrap_text(text: str) -> str:
    return EMOJI_RE.sub(lambda match: WRAPPER.format(match.group(0)), text)


def _hides_content(name: str, attrs: str) -> bool:
    return (
        name in SKIPPED_TAGS
        or bool(_ARIA_HIDDEN_RE.search(attrs))
        or bool(_ROLE_IMG_RE.search(attrs))
    )


def hide_emojis_from_assistive_tech(html: str) -> str:
    """Wrap emojis found in text nodes in <span aria-hidden="true">.

    Attributes, comments, raw text elements (script, style, textarea, title) and
    content already hidden from assistive technologies are left untouched.
    """
    if not EMOJI_RE.search(html):
        return html

    parts: list[str] = []
    stack: list[tuple[str, bool]] = []
    hidden_depth = 0
    position = 0

    def emit_text(text: str) -> None:
        parts.append(text if hidden_depth else _wrap_text(text))

    for token in _TOKEN_RE.finditer(html):
        if token.start() < position:
            continue
        emit_text(html[position : token.start()])
        parts.append(token.group(0))
        position = token.end()

        name = token.group("name")
        if name is None:
            continue
        name = name.lower()

        if token.group("closing"):
            for index in range(len(stack) - 1, -1, -1):
                if stack[index][0] == name:
                    hidden_depth -= sum(flag for _, flag in stack[index:])
                    del stack[index:]
                    break
            continue

        if name in VOID_TAGS or token.group("attrs").rstrip().endswith("/"):
            continue

        if name in RAW_TEXT_TAGS:
            closing = re.compile(rf"</{name}\s*>", re.I).search(html, position)
            end = closing.end() if closing else len(html)
            parts.append(html[position:end])
            position = end
            continue

        hides = not hidden_depth and _hides_content(name, token.group("attrs"))
        stack.append((name, hides))
        hidden_depth += hides

    emit_text(html[position:])
    return "".join(parts)
