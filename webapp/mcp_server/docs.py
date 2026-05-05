from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent / "docs"


@dataclass(frozen=True)
class Doc:
    slug: str
    filename: str
    uri: str
    title: str
    description: str

    @property
    def path(self) -> Path:
        return DOCS_DIR / self.filename


DOCS: tuple[Doc, ...] = (
    Doc(
        slug="about",
        filename="00-about.md",
        uri="qfdmo://about",
        title="À propos du jeu de données",
        description=(
            "Présentation du jeu de données ADEME « Que Faire De Mes Objets et "
            "Déchets » et des cas d'usage."
        ),
    ),
    Doc(
        slug="workflow",
        filename="10-workflow.md",
        uri="qfdmo://workflow",
        title="Workflow recommandé",
        description=(
            "Étapes recommandées pour répondre à une question utilisateur : "
            "localisation, sous-catégorie, action, géocodage, recherche, restitution."
        ),
    ),
    Doc(
        slug="geocoding",
        filename="20-geocoding.md",
        uri="qfdmo://geocoding",
        title="Géocodage avec l'API BAN",
        description=(
            "Comment transformer une adresse française en couple "
            "(longitude, latitude) via l'API Base Adresse Nationale."
        ),
    ),
    Doc(
        slug="search-api",
        filename="30-search-api.md",
        uri="qfdmo://search-api",
        title="Interrogation de l'API ADEME /lines",
        description=(
            "Documentation de l'endpoint /lines : geo_distance, qs, sort, size, "
            "select, exemples."
        ),
    ),
    Doc(
        slug="actions",
        filename="40-actions.md",
        uri="qfdmo://actions",
        title="Codes d'action",
        description=(
            "Liste des actions (preter, emprunter, louer, reparer, donner, "
            "rapporter, …) et quand utiliser chacune."
        ),
    ),
    Doc(
        slug="sous-categories",
        filename="50-sous-categories.md",
        uri="qfdmo://sous-categories",
        title="Codes de sous-catégorie d'objet",
        description=(
            "Liste exhaustive des codes de sous-catégorie utilisés pour filtrer "
            "les acteurs par type d'objet."
        ),
    ),
    Doc(
        slug="sources",
        filename="60-sources.md",
        uri="qfdmo://sources",
        title="Sources de données et paternité",
        description=(
            "Liste des contributeurs au jeu de données et règles de citation."
        ),
    ),
    Doc(
        slug="examples",
        filename="70-examples.md",
        uri="qfdmo://examples",
        title="Exemples concrets",
        description=(
            "Exemples de requêtes complètes pour les cas d'usage les plus " "fréquents."
        ),
    ),
)

DOCS_BY_SLUG: dict[str, Doc] = {d.slug: d for d in DOCS}
DOCS_BY_URI: dict[str, Doc] = {d.uri: d for d in DOCS}


def read(doc: Doc) -> str:
    return doc.path.read_text(encoding="utf-8")
