from bs4 import BeautifulSoup
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

NEW_WINDOW_MENTION = "nouvelle fenêtre"


def announce_new_window_links(html: str, mention: str = NEW_WINDOW_MENTION) -> str:
    """Give every ``target="_blank"`` link without a mention of the new window a
    ``title`` made of its text and the mention (RGAA 10.2: the DSFR
    external icon is CSS only, so it vanishes when stylesheets are disabled).
    A link without text falls back on the ``alt`` of its image, or is left as is."""
    if 'target="_blank"' not in html:
        return html

    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a", target="_blank"):
        text = (
            " ".join(link.get_text(" ").split())
            or " ".join(image.get("alt", "") for image in link.find_all("img")).strip()
        )
        if not text or mention.lower() in text.lower():
            continue
        title = link.get("title", "").strip()
        if mention.lower() in title.lower():
            continue
        link["title"] = f"{title or text} - {mention}"
    return str(soup)


@register.filter
def announce_new_window(html: str, mention: str = NEW_WINDOW_MENTION) -> str:
    return mark_safe(announce_new_window_links(html, mention))
