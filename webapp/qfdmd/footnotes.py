import re
from collections import Counter

CALL_RE = re.compile(r'<a href="#[\w-]+">\s*(\d{1,2})\s*</a>')
NOTE_RE = re.compile(r"<p(?: [^>]*)?>\s*\((\d{1,2})\)\s*(.*?)</p>", re.DOTALL)
NOTES_RUN_RE = re.compile(r"(?:" + NOTE_RE.pattern + r"\s*)+", re.DOTALL)


def make_footnotes_accessible(html: str) -> str:
    """Rewrite legacy CMS footnotes to the accessible footnote pattern.

    CMS content writes a call as a link to a generic anchor whose text is the
    note number, and the notes as paragraphs starting with ``(n)``. A call and a
    note are only rewritten when both exist for the same number.
    """
    if 'href="#' not in html:
        return html

    shared = {n for n in CALL_RE.findall(html)} & {n for n, _ in NOTE_RE.findall(html)}
    if not shared:
        return html

    seen: Counter = Counter()

    def rewrite_call(match: re.Match) -> str:
        number = match.group(1)
        if number not in shared:
            return match.group(0)
        seen[number] += 1
        suffix = "" if seen[number] == 1 else f"-{seen[number]}"
        return (
            f'<sup><a href="#note-{number}" id="appel-note-{number}{suffix}" '
            f'aria-label="Note de bas de page {number}" '
            f'aria-describedby="note-{number}">{number}</a></sup>'
        )

    def rewrite_run(run: re.Match) -> str:
        items = []
        for note in NOTE_RE.finditer(run.group(0)):
            number, content = note.group(1), note.group(2)
            if number not in shared:
                return run.group(0)
            items.append(
                f'<li id="note-{number}" tabindex="-1">'
                f'<a href="#appel-note-{number}" '
                f'aria-label="[{number}] retour au texte">[{number}]</a> '
                f"{content}</li>"
            )
        return (
            '<ol class="fr-raw-list" aria-label="Notes de bas de page">'
            + "".join(items)
            + "</ol>"
        )

    html = CALL_RE.sub(rewrite_call, html)
    return NOTES_RUN_RE.sub(rewrite_run, html)
