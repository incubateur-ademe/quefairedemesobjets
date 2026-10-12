"""Detail of a groupe (modal of the review screen): the acteur as displayed on the
map, the points of the localisation tab and the identifiers of the Annuaire
Entreprises tab."""

from data.models.suggestion import SuggestionGroupe
from data.models.suggestions.source import SuggestionSourceModel
from data.revue.annuaire import identifiants
from data.revue.services import can_create_localisation
from data.revue.lignes import ACTEUR, serialize_groupe
from data.revue.policies import PARENT, REVISION, ReviewPolicy
from qfdmo.models.acteur import DisplayedActeur

LATLONG = ("latitude", "longitude")

DISPLAYED_FIELDS = [
    "identifiant_unique",
    "nom",
    "nom_commercial",
    "nom_officiel",
    "acteur_type_code",
    "source_code",
    "statut",
    "siret",
    "siren",
    "naf_principal",
    "adresse",
    "adresse_complement",
    "code_postal",
    "ville",
    "latitude",
    "longitude",
    "url",
    "email",
    "telephone",
    "horaires_osm",
    "horaires_description",
    "public_accueilli",
    "reprise",
    "uniquement_sur_rdv",
    "consignes_dacces",
    "lieu_prestation",
    "description",
    "commentaires",
]


def _displayed_acteur(groupe: SuggestionGroupe) -> DisplayedActeur | None:
    identifiant = (
        groupe.parent_revision_acteur_id
        or groupe.revision_acteur_id
        or groupe.acteur_id
    )
    if not identifiant:
        return None
    return DisplayedActeur.objects.filter(identifiant_unique=identifiant).first()


def _displayed_fields(displayed: DisplayedActeur | None) -> list[dict]:
    if displayed is None:
        return []
    values = SuggestionSourceModel.from_acteur(
        displayed, fields_to_include=DISPLAYED_FIELDS
    )
    return [
        {"champ": champ, "valeur": getattr(values, champ, None) or ""}
        for champ in DISPLAYED_FIELDS
    ]


def _point(key: str, lat, lng, draggable: bool = False) -> dict | None:
    try:
        return {
            "key": key,
            "latitude": float(lat),
            "longitude": float(lng),
            "draggable": draggable,
        }
    except (TypeError, ValueError):
        return None


def localisation(
    groupe: SuggestionGroupe, serialized: dict, policy: ReviewPolicy
) -> dict:
    """Points of the map, as in the localisation tab of the admin:
    - Origin (grey): acteur as saved in DB;
    - Acteur (green « A »): acteur suggested by the source;
    - RevisionActeur (blue « ▶ »): proposed correction, else current revision;
    - ParentRevisionActeur (red « ⏩ »): proposed parent, else current parent.
    Correction and parent markers are draggable when the (latitude, longitude)
    ligne of the groupe may be corrected on that object."""
    ligne = next(
        (ligne for ligne in serialized["lignes"] if tuple(ligne["champs"]) == LATLONG),
        None,
    )
    capacites = ligne["capacites"] if ligne else {}
    proposals = {
        su.suggestion_modele: su.valeurs
        for su in groupe.suggestion_unitaires.all()
        if tuple(su.champs) == LATLONG
    }

    def current(instance):
        if instance is None:
            return None
        return getattr(instance, "latitude", None), getattr(instance, "longitude", None)

    acteur = groupe.get_acteur_or_none()
    revision = groupe.get_revision_acteur_or_none()
    parent = groupe.get_parent_revision_acteur_or_none()
    candidates = [
        ("Origin", current(acteur), False),
        ("Acteur", proposals.get(ACTEUR), False),
        (
            REVISION,
            proposals.get(REVISION) or current(revision),
            bool(capacites.get("corriger_correction")),
        ),
        (
            PARENT,
            proposals.get(PARENT) or current(parent),
            bool(capacites.get("corriger_parent")),
        ),
    ]
    points = []
    for key, coordinates, draggable in candidates:
        if coordinates and all(coordinates):
            point = _point(key, *coordinates, draggable=draggable)
            if point:
                points.append(point)
    return {
        "points": points,
        "ligne": ligne["key"] if ligne else None,
        # No proposed correction of the localisation (SU latitude/longitude on
        # RevisionActeur) yet: the reviewer may add one, even when the acteur
        # already has a correction (RevisionActeur)
        "creer_correction": REVISION not in proposals
        and (ligne is None or bool(capacites.get("corriger_correction")))
        and can_create_localisation(groupe, policy, REVISION),
    }


def serialize_groupe_detail(groupe: SuggestionGroupe, policy: ReviewPolicy) -> dict:
    serialized = serialize_groupe(groupe, policy)
    displayed = _displayed_acteur(groupe)
    return {
        **serialized,
        "acteur_affiche": _displayed_fields(displayed),
        "localisation": localisation(groupe, serialized, policy),
        "annuaire": identifiants(groupe, displayed),
    }
