import re
from dataclasses import dataclass

MARKERS = ("✅", "🟠", "‼", "➡", "•")
BULLET_PARAGRAPH_RE = re.compile(
    r"<p((?: [^>]*)?)>(\s*(?:<(?:b|strong)>\s*)?"
    r"(" + "|".join(MARKERS) + r")️?.*?)</p>",
    re.DOTALL,
)


CLASS_ATTRIBUTE_RE = re.compile(r' class="([^"]*)"')


@dataclass(frozen=True)
class _Bullet:
    start: int
    end: int
    marker: str
    attributes: str
    content: str


def make_bullet_paragraphs_lists(html: str) -> str:
    """Turn consecutive paragraphs sharing the same bullet marker into a list.

    CMS content fakes lists with one paragraph per line, each starting with the
    same emoji or bullet. Only runs of two or more paragraphs with the same
    marker are rewritten; the marker stays in the text.
    """
    bullets = [
        _Bullet(m.start(), m.end(), m.group(3), m.group(1), m.group(2))
        for m in BULLET_PARAGRAPH_RE.finditer(html)
    ]

    runs: list[list[_Bullet]] = []
    for bullet in bullets:
        previous = runs[-1][-1] if runs else None
        if (
            previous
            and previous.marker == bullet.marker
            and not html[previous.end : bullet.start].strip()
        ):
            runs[-1].append(bullet)
        else:
            runs.append([bullet])

    parts: list[str] = []
    cursor = 0
    for run in (r for r in runs if len(r) > 1):
        items = "".join(
            f"<li{CLASS_ATTRIBUTE_RE.sub('', b.attributes)}>{b.content}</li>"
            for b in run
        )
        classes = " ".join(
            ["fr-raw-list", *CLASS_ATTRIBUTE_RE.findall(run[0].attributes)]
        )
        parts.append(html[cursor : run[0].start])
        parts.append(f'<ul class="{classes}">{items}</ul>')
        cursor = run[-1].end
    parts.append(html[cursor:])
    return "".join(parts)
