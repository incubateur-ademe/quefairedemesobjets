"""Open data of the places: the perimeter and the columns of the acteurs
dataset published on data.ademe.fr."""

from django.conf import settings
from django.db.models import Exists, OuterRef
from ninja import Field, Schema

from qfdmo.models.acteur import DataLicense, Source


def open_data(acteurs):
    """Acteurs that may be redistributed: at least one source under an open
    licence.

    Same rule as the opendata mart (`marts_opendata_filtered_acteur`): an
    acteur is published if its source is open, and a parent if one of its
    children is. `sources` already holds the children's sources of a parent,
    so one EXISTS covers both.
    """
    open_sources = Source.objects.filter(
        displayed_acteurs=OuterRef("pk"), licence=DataLicense.OPEN_LICENSE
    )
    return acteurs.filter(Exists(open_sources))


def for_the_api(acteurs):
    """A place and everything the API exposes, without cascading queries: the
    opendata columns need every relation."""
    return (
        acteurs.for_the_detail()
        .select_related("epci")
        .prefetch_related(
            "proposition_services__action",
            "proposition_services__sous_categories",
            "acteur_services",
            "perimetre_adomiciles",
        )
        .with_bonus()
    )


class PropositionSchema(Schema):
    action: str
    sous_categories: list[str]


class PaterniteSchema(Schema):
    code: str | None = None
    nom: str
    url: str | None = None
    logo: str | None = None


class PerimetreSchema(Schema):
    type: str
    valeur: str


class LieuSchema(Schema):
    """A place, with the columns of the opendata dataset.

    Field names follow the CSV published on data.ademe.fr so that a reuser
    can switch between the two without a mapping. Not carried over: the
    columns data.ademe.fr computes after export (région, département, état
    SIRENE) and the per-action columns, which `propositions_de_services`
    already holds.
    """

    identifiant: str = Field(..., alias="uuid")
    paternite: list[PaterniteSchema]
    nom: str
    nom_commercial: str | None = None
    siren: str | None = None
    siret: str | None = None
    description: str | None = None
    type_dacteur: str | None = Field(None, alias="acteur_type.code")
    site_web: str | None = Field(None, alias="url")
    telephone: str | None = None
    adresse: str | None = None
    complement_dadresse: str | None = Field(None, alias="adresse_complement")
    code_postal: str | None = None
    ville: str | None = None
    code_commune: str | None = Field(None, alias="code_commune_insee")
    code_epci: str | None = Field(None, alias="epci.code")
    nom_epci: str | None = Field(None, alias="epci.nom")
    latitude: float | None = None
    longitude: float | None = None
    qualites_et_labels: str
    propose_le_bonus_reparation: bool
    public_accueilli: str | None = None
    reprise: str | None = None
    exclusivite_de_reprisereparation: bool | None = None
    uniquement_sur_rdv: bool | None = None
    type_de_services: str
    lieu_prestation: str | None = None
    perimetreadomicile: list[PerimetreSchema]
    consignes_dacces: str | None = None
    horaires_description: str | None = None
    horaires_osm: str | None = None
    propositions_de_services: list[PropositionSchema]
    date_de_derniere_modification: str

    @staticmethod
    def resolve_paternite(obj) -> list[dict]:
        """Same contributors as the dataset, in the same order: the site,
        ADEME, then the open sources by name."""
        sources = sorted(
            {
                source
                for source in obj.sources.all()
                if source.licence == DataLicense.OPEN_LICENSE
            },
            key=lambda source: source.libelle,
        )
        return [
            {"nom": "Que faire de mes objets et déchets", "url": settings.BASE_URL},
            {"nom": "ADEME", "url": "https://www.ademe.fr"},
            *(
                {
                    "code": source.code,
                    "nom": source.libelle,
                    "url": source.url or None,
                    "logo": source.logo_file_absolute_url or None,
                }
                for source in sources
            ),
        ]

    @staticmethod
    def resolve_latitude(obj) -> float | None:
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_longitude(obj) -> float | None:
        return obj.location.x if obj.location else None

    @staticmethod
    def resolve_qualites_et_labels(obj) -> str:
        return "|".join(sorted({label.code for label in obj.labels.all()}))

    @staticmethod
    def resolve_propose_le_bonus_reparation(obj) -> bool:
        # Annotated by `with_bonus()`; a bare instance has no bonus.
        return bool(getattr(obj, "bonus", False))

    @staticmethod
    def resolve_type_de_services(obj) -> str:
        return "|".join(sorted({service.code for service in obj.acteur_services.all()}))

    @staticmethod
    def resolve_perimetreadomicile(obj) -> list[dict]:
        return [
            {"type": perimetre.type, "valeur": perimetre.valeur}
            for perimetre in obj.perimetre_adomiciles.all()
        ]

    @staticmethod
    def resolve_propositions_de_services(obj) -> list[dict]:
        return [
            {
                "action": proposition.action.code,
                "sous_categories": sorted(
                    sous_categorie.code
                    for sous_categorie in proposition.sous_categories.all()
                ),
            }
            for proposition in obj.proposition_services.all()
        ]

    @staticmethod
    def resolve_date_de_derniere_modification(obj) -> str:
        return obj.modifie_le.date().isoformat()


class GesteSchema(Schema):
    code: str
    libelle: str
    libelle_court: str | None = None
    couleur: str | None = None
