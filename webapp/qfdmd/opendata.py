"""Open data of the fiches: produits and their consignes (#3266, #3284).

Two tables joined on `identifiant_produit`, in the conventions of the acteurs
CSV published on data.ademe.fr: snake_case columns without accents, `|`
between the values of a cell, an empty cell when unknown. Two columns pivot
to that dataset: `sous_categories` (codes of `qfdmo_souscategorieobjet`) and
`gestes` (Action codes, the per-action columns of the acteurs CSV).

The API v1 serves the same rows as JSON and as CSV (`qfdmd/api.py`); the
weekly export DAG fetches the CSV and publishes it on S3.
"""

import csv
import re
from html import unescape

from django.utils.html import strip_tags

from qfdmd.models import ProduitPage

PRODUIT_COLUMNS = [
    "identifiant",
    "nom",
    "url",
    "type",
    "identifiant_famille",
    "synonymes",
    "sous_categories",
    "date_de_derniere_modification",
]

CONSIGNE_COLUMNS = [
    "identifiant",
    "identifiant_produit",
    "ordre",
    "titre",
    "contenu",
    "contenu_texte",
    "gestes",
    "etat",
    "lieu_de_depot",
    "bonus_reparation",
    "lien_url",
]


def produits():
    """The published fiches, familles included, by identifier."""
    return (
        ProduitPage.objects.live()
        .public()
        .order_by("pk")
        .prefetch_related("search_tags", "sous_categorie_objet")
    )


def produit_row(page: ProduitPage) -> dict:
    parent = page.get_parent().specific
    # Pages imported by script may never have been published through the admin.
    modified = page.last_published_at or page.latest_revision_created_at
    return {
        "identifiant": page.pk,
        "nom": page.title,
        "url": page.full_url or "",
        "type": "dechet" if page.usage_unique else "objet",
        "identifiant_famille": parent.pk if isinstance(parent, ProduitPage) else None,
        "synonymes": "|".join(sorted(tag.name for tag in page.search_tags.all())),
        "sous_categories": "|".join(
            sorted(sc.code for sc in page.sous_categorie_objet.all())
        ),
        "date_de_derniere_modification": (
            modified.date().isoformat() if modified else ""
        ),
    }


def consigne_rows(page: ProduitPage) -> list[dict]:
    """One row per consigne of the page, `ordre` being its reading position."""
    rows = []
    for ordre, child in enumerate(page.consignes, start=1):
        value = child.value
        # `str()` expands the internal page links of the rich text into URLs.
        contenu = str(value["contenu"])
        rows.append(
            {
                "identifiant": child.id,
                "identifiant_produit": page.pk,
                "ordre": ordre,
                "titre": value["titre"],
                "contenu": contenu,
                "contenu_texte": plain_text(contenu),
                "gestes": "|".join(value["gestes"]),
                "etat": value["etat"] or "",
                "lieu_de_depot": (
                    value["lieu_de_depot"].code if value["lieu_de_depot"] else ""
                ),
                "bonus_reparation": bool(value["bonus_reparation"]),
                "lien_url": (value["lien"].full_url or "") if value["lien"] else "",
            }
        )
    return rows


def produit_rows() -> list[dict]:
    return [produit_row(page) for page in produits()]


def all_consigne_rows() -> list[dict]:
    return [row for page in produits() for row in consigne_rows(page)]


def plain_text(html: str) -> str:
    """The rich text without tags, one line per paragraph or list item,
    list items prefixed with `- ` so a list stays readable in a cell."""
    text = re.sub(r"<li[^>]*>", "- ", html)
    text = re.sub(r"</(p|li|ul|ol|h\d)>", "\n", text)
    text = unescape(strip_tags(text))
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def write_csv(rows: list[dict], columns: list[str], stream) -> None:
    """The cells as the acteurs CSV writes them: `true`/`false`, empty for
    a missing value."""
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _cell(row.get(column)) for column in columns})


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
