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

_VARIATION_SELECTOR = "\ufe0f"
_ZERO_WIDTH_JOINER = "\u200d"
_COMBINING_KEYCAP = "\u20e3"
_SKIN_TONES = "\U0001f3fb-\U0001f3ff"
_STAR = "\u2b50"

# Symbols rendered as an emoji without U+FE0F (Emoji_Presentation).
_EMOJI_BASE = (
    "\u231a\u231b\u23e9-\u23ec\u23f0\u23f3\u25fd\u25fe\u2614\u2615\u2648-\u2653"
    "\u267f\u2693\u26a1\u26aa\u26ab\u26bd\u26be\u26c4\u26c5\u26ce\u26d4\u26ea"
    "\u26f2\u26f3\u26f5\u26fa\u26fd\u2705\u270a\u270b\u2728\u274c\u274e"
    "\u2753-\u2755\u2757\u2795-\u2797\u27b0\u27bf\u2b1b\u2b1c\u2b50\u2b55"
    "\U0001f000-\U0001faff"
)
# Symbols rendered as text (©, ♥, ✔, ➡, arrows...) unless followed by U+FE0F.
_TEXT_DEFAULT_BASE = (
    "\u00a9\u00ae\u203c\u2049\u2122\u2139\u2194-\u2199\u21a9\u21aa\u24c2"
    "\u25aa\u25ab\u25b6\u25c0\u25fb\u25fc\u2328\u23cf\u23ed-\u23ef\u23f1\u23f2"
    "\u23f8-\u23fa\u2600-\u2604\u260e\u2611\u2618\u261d\u2620\u2622\u2623"
    "\u2626\u262a\u262e\u262f\u2638-\u263a\u2640\u2642\u265f\u2660\u2663"
    "\u2665\u2666\u2668\u267b\u267e\u2692\u2694-\u2697\u2699\u269b\u269c"
    "\u26a0\u26a7\u26b0\u26b1\u26c8\u26cf\u26d1\u26d3\u26e9\u26f0\u26f1\u26f4"
    "\u26f7-\u26f9\u2702\u2708\u2709\u270c\u270d\u270f\u2712\u2714\u2716"
    "\u271d\u2721\u2733\u2734\u2744\u2747\u2763\u2764\u27a1\u2934\u2935"
    "\u2b05-\u2b07\u3030\u303d\u3297\u3299"
)
_SINGLE_EMOJI = (
    f"(?:[{_EMOJI_BASE}]{_VARIATION_SELECTOR}?|"
    f"[{_TEXT_DEFAULT_BASE}]{_VARIATION_SELECTOR})[{_SKIN_TONES}]?"
)
_EMOJI_SEQUENCE = f"(?!{_STAR}){_SINGLE_EMOJI}(?:{_ZERO_WIDTH_JOINER}{_SINGLE_EMOJI})*"
_FLAG = "[\U0001f1e6-\U0001f1ff]{2}"
_TAG_FLAG = "\U0001f3f4[\U000e0020-\U000e007e]+\U000e007f"
_KEYCAP = f"[0-9#*]{_VARIATION_SELECTOR}?{_COMBINING_KEYCAP}"

_STARS = f"(?P<stars>(?:{_STAR}{_VARIATION_SELECTOR}?)+)"
_EMOJIS = f"(?P<emojis>(?:{_TAG_FLAG}|{_KEYCAP}|{_FLAG}|{_EMOJI_SEQUENCE})+)"
EMOJI_RE = re.compile(rf"(?:{_STARS}|{_EMOJIS})(?P<space> (?=\S))?")

_TOKEN_RE = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<![^>]*>|<\?.*?\?>"
    r"|<(?P<closing>/?)(?P<name>[a-zA-Z][^\s/>]*)(?P<attrs>(?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>",
    re.DOTALL,
)
_ARIA_HIDDEN_RE = re.compile(r"""\saria-hidden\s*=\s*["']?true["']?""", re.I)
_ROLE_IMG_RE = re.compile(r"""\srole\s*=\s*["']?img["']?""", re.I)

HIDDEN = '<span aria-hidden="true"{style}>{}</span>'
RATING = '<span role="img" aria-label="{count} {unit}"{style}>{}</span>'
# Keeps the space that follows the emoji when the span is a flex item.
KEEP_SPACE_STYLE = ' style="white-space: pre-wrap"'


def _wrap_match(match: re.Match) -> str:
    style = KEEP_SPACE_STYLE if match.group("space") else ""
    if match.group("stars"):
        count = len(match.group("stars").replace(_VARIATION_SELECTOR, ""))
        unit = "étoile" if count == 1 else "étoiles"
        return RATING.format(match.group(0), count=count, unit=unit, style=style)
    return HIDDEN.format(match.group(0), style=style)


def _wrap_text(text: str) -> str:
    return EMOJI_RE.sub(_wrap_match, text)


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
