"""Fill the "Grille de consignes" block of a fiche from its existing content.

The consignes of a fiche were written as free cards before the typed block
existed (#3284), always in the same place: the **first row of cards** of the
body, right after the introduction and before the map. Every fiche follows
that layout (checked on the 45 live ones), so that row is what converts;
later cards ("Des emballages pensés pour être réemployés", "Que faire de mon
canapé ?") are never consignes.

The conversion is deterministic, the rules being those of the spec:

- objet: the état is the first badge (Réparable, Bon état, Mauvais état),
  or the title when the card has no badge; the gestes follow the état; the
  bonus is a badge naming it;
- déchet: the geste is `trier` ("déposer"), or `rapporter` when the card
  says to bring the product back; the lieu de dépôt is the first badge that
  names a lieu.

Title, content and link are copied verbatim. A card whose fields cannot be
resolved stays where it is and is reported to the editor. The row moves
into the grid in a **draft revision**: nothing is published until an editor
has read it.

Entry points: `plan_conversion()` computes without writing, `apply_plan()`
writes the draft. The admin action in `qfdmd/views.py` chains the two.
"""

import json
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field

from django.utils.html import strip_tags
from wagtail.log_actions import log
from wagtail.models import Page

from qfdmd.blocks import ETAT_CHOICES
from qfdmd.models import LieuDeDepot, ProduitPage

logger = logging.getLogger(__name__)

MAX_PER_GRID = 4
# Width of a grid built from lone cards, by their number (spec #3284).
COLUMN_WIDTH_FOR = {1: "12", 2: "6", 3: "4", 4: "3"}

# Blocks that hold cards: a grid of them, or one on its own.
CARD_BLOCK_TYPES = frozenset({"item_grid", "card"})
# Blocks allowed before the first row of cards: the introduction.
INTRO_BLOCK_TYPES = frozenset({"paragraph", "separator", "anchor"})

# The badges of the fiches, normalised (lower case, no accent), and the état
# they stand for.
ETAT_BY_BADGE = {
    "reparable": "reparable",
    "bon etat": "bon_etat",
    "mauvais etat": "mauvais_etat",
}
# The title of a card without badge, on the objets fiches: "Réparer",
# "Donner ou revendre", "Déposer".
ETAT_BY_TITLE_WORD = {
    "reparer": "reparable",
    "donner": "bon_etat",
    "revendre": "bon_etat",
    "vendre": "bon_etat",
    "deposer": "mauvais_etat",
}
# Spec: the gestes of an objet follow its état. "Déposer" is the code `trier`.
GESTES_BY_ETAT = {
    "reparable": ["reparer"],
    "bon_etat": ["donner", "revendre", "preter", "louer"],
    "mauvais_etat": ["trier"],
}
BONUS_WORDS = "bonus reparation"
RAPPORTER_WORDS = ("rapport", "ramen")  # rapporter, rapportez, ramener


@dataclass
class Consigne:
    """A card of the first row, converted."""

    block_id: str
    item_index: int | None
    value: dict


@dataclass
class Unresolved:
    """A card of the first row that stays where it is, and why."""

    titre: str
    reason: str


@dataclass
class Plan:
    consignes: list[Consigne] = field(default_factory=list)
    unresolved: list[Unresolved] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def first_row_of_cards(page: ProduitPage) -> list[dict]:
    """The cards of the first row of the body, each with its address.

    The row starts at the first card block after the introduction and ends
    at the first block that is not a card block. A grid yields one entry per
    card (`item_index`), a lone card one entry (`item_index` None). Tiles and
    other grid items are not cards and are left out.
    """
    raw = page.body.get_prep_value()
    cards, started = [], False
    for block in raw:
        if block["type"] in CARD_BLOCK_TYPES:
            started = True
            if block["type"] == "card":
                cards.append(
                    {
                        "block_id": block["id"],
                        "item_index": None,
                        "card": block["value"],
                    }
                )
            else:
                for index, item in enumerate(block["value"].get("items", [])):
                    if item.get("type") == "card":
                        cards.append(
                            {
                                "block_id": block["id"],
                                "item_index": index,
                                "card": item["value"],
                            }
                        )
        elif started or block["type"] not in INTRO_BLOCK_TYPES:
            break
    return cards


def plan_conversion(page: ProduitPage) -> Plan:
    """Convert the first row, in memory. Nothing is written."""
    plan = Plan()
    lieux = {normalise(lieu.libelle): lieu for lieu in LieuDeDepot.objects.all()}
    for source in first_row_of_cards(page):
        card = source["card"]
        titre = (card.get("title") or "").strip()
        if not titre:
            plan.unresolved.append(Unresolved("(sans titre)", "carte sans titre"))
            continue
        badges = [normalise(text) for text in badge_texts(card)]
        typed = (_typed_for_dechet if page.usage_unique else _typed_for_objet)(
            card, badges, lieux, plan
        )
        if typed is None:
            continue
        plan.consignes.append(
            Consigne(
                source["block_id"],
                source["item_index"],
                {**_card_content(card), **typed},
            )
        )
    return plan


def _typed_for_objet(
    card: dict, badges: list[str], lieux: dict, plan: Plan
) -> dict | None:
    """Spec rules for an objet. A card that talks like a déchet (a lieu de
    dépôt as badge, or named in its text without any état) is not converted:
    the fiche's « À usage unique » flag is probably wrong, and guessing an
    état would publish a false one."""
    titre = card["title"].strip()
    if any(b in lieux for b in badges):
        plan.unresolved.append(
            Unresolved(
                titre,
                "badge de lieu de dépôt sur une fiche objet : la fiche est-elle un"
                " déchet (« À usage unique ») ?",
            )
        )
        return None
    etat = next((ETAT_BY_BADGE[b] for b in badges if b in ETAT_BY_BADGE), None)
    if etat is None and not badges:
        text = normalise(f"{titre} {strip_tags(card.get('description') or '')}")
        if any(lieu in text for lieu in lieux):
            plan.unresolved.append(
                Unresolved(
                    titre,
                    "la carte nomme un lieu de dépôt sans badge d'état : la fiche"
                    " est-elle un déchet (« À usage unique ») ?",
                )
            )
            return None
        words = normalise(titre).split()
        etat = next(
            (ETAT_BY_TITLE_WORD[w] for w in words if w in ETAT_BY_TITLE_WORD), None
        )
        if etat:
            plan.notes.append(f"« {titre} » : état déduit du titre, aucun badge")
    if etat is None:
        plan.unresolved.append(
            Unresolved(titre, "aucun badge ni titre ne donne l'état de l'objet")
        )
        return None
    return {
        "gestes": list(GESTES_BY_ETAT[etat]),
        "etat": etat,
        "lieu_de_depot": None,
        "bonus_reparation": any(BONUS_WORDS in b for b in badges),
    }


def _typed_for_dechet(
    card: dict, badges: list[str], lieux: dict, plan: Plan
) -> dict | None:
    """Spec rules for a déchet. An état badge means the fiche is really an
    objet: the card is not converted."""
    titre = card["title"].strip()
    if any(b in ETAT_BY_BADGE for b in badges):
        plan.unresolved.append(
            Unresolved(
                titre,
                "badge d'état sur une fiche déchet : la fiche est-elle un objet"
                " (décocher « À usage unique ») ?",
            )
        )
        return None
    lieu = next((lieux[b] for b in badges if b in lieux), None)
    if lieu is None and badges:
        plan.notes.append(
            f"« {titre} » : aucun lieu de dépôt ne correspond au badge "
            f"« {badge_texts(card)[0]} »"
        )
    text = normalise(f"{titre} {strip_tags(card.get('description') or '')}")
    rapporter = any(word in text for word in RAPPORTER_WORDS)
    return {
        "gestes": ["rapporter"] if rapporter else ["trier"],
        "etat": None,
        "lieu_de_depot": lieu.pk if lieu else None,
        "bonus_reparation": False,
    }


def apply_plan(page: ProduitPage, plan: Plan, user=None) -> int:
    """Move the converted cards into grids of consignes, in a draft.

    A grid emptied by the move disappears, a grid partly moved keeps its
    other cards; the new grid takes the place of the first card that moved
    and the width of the grid it came from. Returns the number written.
    """
    if not plan.consignes:
        return 0
    moved = {(c.block_id, c.item_index) for c in plan.consignes}
    raw = page.body.get_prep_value()
    width = _source_width(raw, moved)
    grids = [
        {
            "type": "consignes",
            "value": {
                "column_width": width or COLUMN_WIDTH_FOR.get(len(chunk), "4"),
                # An id per item: the CMS would assign one on save, and the
                # open data publishes it.
                "consignes": [
                    {"type": "item", "id": str(uuid.uuid4()), "value": c.value}
                    for c in chunk
                ],
            },
        }
        for chunk in _chunks(plan.consignes, MAX_PER_GRID)
    ]

    body, inserted = [], False
    for block in raw:
        remaining = _without_moved(block, moved)
        if remaining is not block and not inserted:
            body.extend(grids)
            inserted = True
        if remaining is not None:
            body.append(remaining)

    page.body = json.dumps(body)
    revision = page.save_revision(user=user)
    log(
        instance=page,
        action="qfdmd.generate_consignes",
        user=user,
        revision=revision,
        data={
            "consignes": len(plan.consignes),
            "non_converties": [u.titre for u in plan.unresolved],
        },
    )
    return len(plan.consignes)


def badge_texts(card: dict) -> list[str]:
    """The texts of the badges and tags of the card's top detail, in order."""
    texts = []

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            text = value.get("text") or value.get("label")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
            else:
                for child in value.values():
                    walk(child)

    walk(card.get("top_detail_badges_tags") or [])
    return texts


def normalise(text: str) -> str:
    """Lower case, no accent, no emoji or punctuation, single spaces: the
    badges are typed by hand ("BAC DE TRI", "✅ Déposer…", "% Bonus")."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
    return text.casefold().strip()


def _card_content(card: dict) -> dict:
    """Title, content and link of the card, copied as they are stored."""
    link = card.get("link") or {}
    lien = link.get("page") if link.get("link_type") == "page" else None
    return {
        "titre": card["title"].strip(),
        "contenu": card.get("description") or "",
        "lien": lien if lien and Page.objects.filter(pk=lien).exists() else None,
    }


def _source_width(raw: list, moved: set) -> str | None:
    """The column width of the first grid a card moved from, if any."""
    grids = {block["id"]: block for block in raw if block["type"] == "item_grid"}
    for block_id, _ in sorted(moved, key=lambda key: str(key)):
        if block_id in grids:
            return grids[block_id]["value"].get("column_width") or None
    return None


def _without_moved(block: dict, moved: set) -> dict | None:
    """The block once its moved cards are gone: itself when untouched, a
    lighter grid, or None when nothing is left."""
    block_id = block.get("id")
    if block["type"] == "item_grid":
        items = block["value"].get("items", [])
        kept = [it for i, it in enumerate(items) if (block_id, i) not in moved]
        if len(kept) == len(items):
            return block
        if not kept:
            return None
        return {**block, "value": {**block["value"], "items": kept}}
    return None if (block_id, None) in moved else block


def _chunks(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]


# Sanity: every état of the rules exists in the block's choices.
assert set(GESTES_BY_ETAT) == {code for code, _ in ETAT_CHOICES}
