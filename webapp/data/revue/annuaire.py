"""Annuaire des entreprises: identifiers of a groupe and lookup in the public API
« Recherche d'entreprises » (https://recherche-entreprises.api.gouv.fr), proxied
by the server (cache, timeout, errors) for the modal of the review screen."""

import logging
import re

import requests
from django.core.cache import cache

from data.models.suggestion import SuggestionGroupe
from data.revue.errors import RevueApiError
from data.revue.lignes import ACTEUR
from data.revue.policies import PARENT, REVISION

logger = logging.getLogger(__name__)

API_URL = "https://recherche-entreprises.api.gouv.fr/search"
TIMEOUT = 5
CACHE_SECONDS = 24 * 3600
IDENTIFIANTS = ("siret", "siren")
PATTERNS = {"siret": re.compile(r"^\d{14}$"), "siren": re.compile(r"^\d{9}$")}

# Sources of a value, in the order of precedence of the tab
SOURCES = [
    ("corrige", "Valeur corrigée (acteur affiché)"),
    ("parent", "Parent"),
    ("correction", "Correction"),
    ("acteur", "Acteur importé"),
]


def _clean(value) -> str:
    return re.sub(r"\s", "", str(value or ""))


def identifiants(groupe: SuggestionGroupe, displayed) -> dict[str, list[dict]]:
    """For SIRET and SIREN, the values to look up, each with its source:
    - the corrected value (acteur displayed), if it exists;
    - the parent value, if it exists and differs from the corrected one;
    - the correction value, if it exists and differs from the previous ones;
    - the acteur importé value, if it differs from the previous ones.
    The value of an object is its proposition when there is one, otherwise its
    current value."""
    proposals = {}
    for su in groupe.suggestion_unitaires.all():
        for champ, valeur in zip(su.champs, su.valeurs):
            if champ in IDENTIFIANTS:
                proposals[(su.suggestion_modele, champ)] = valeur

    objects = {
        "corrige": (None, displayed),
        "parent": (PARENT, groupe.get_parent_revision_acteur_or_none()),
        "correction": (REVISION, groupe.get_revision_acteur_or_none()),
        "acteur": (ACTEUR, groupe.get_acteur_or_none()),
    }
    result = {}
    for champ in IDENTIFIANTS:
        seen: set[str] = set()
        candidates = []
        for source, label in SOURCES:
            modele, instance = objects[source]
            proposed = proposals.get((modele, champ)) if modele else None
            valeur = _clean(
                proposed if proposed is not None else getattr(instance, champ, "")
            )
            if valeur and valeur not in seen:
                seen.add(valeur)
                candidates.append(
                    {
                        "source": source,
                        "label": label,
                        "valeur": valeur,
                        "propose": proposed is not None,
                    }
                )
        result[champ] = candidates
    return result


def _etat_entreprise(etat: str | None) -> str:
    # Unité légale: A (active) or C (cessée)
    return "actif" if etat in (None, "A") else "inactif"


def _etat_etablissement(etat: str | None) -> str:
    # Établissement: A (actif) or F (fermé)
    return "actif" if etat in (None, "A") else "ferme"


def _etablissement(data: dict, nom_entreprise: str | None) -> dict:
    enseignes = data.get("liste_enseignes") or []
    return {
        "siret": data.get("siret") or "",
        "nom": data.get("nom_commercial")
        or (enseignes[0] if enseignes else None)
        or nom_entreprise
        or "",
        "adresse": data.get("adresse") or "",
        "activite_code": data.get("activite_principale") or "",
        "etat": _etat_etablissement(data.get("etat_administratif")),
        "est_siege": bool(data.get("est_siege")),
        "latitude": _float(data.get("latitude")),
        "longitude": _float(data.get("longitude")),
    }


def _float(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _search(query: str) -> dict:
    key = f"revue:annuaire:{query}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        response = requests.get(
            API_URL,
            params={"q": query, "per_page": 1, "minimal": "false"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Annuaire des entreprises indisponible ({query}): {e}")
        raise RevueApiError(
            502, "annuaire_unavailable", "Annuaire des entreprises indisponible"
        ) from e
    cache.set(key, data, CACHE_SECONDS)
    return data


def lookup(champ: str, valeur: str) -> dict:
    """Entreprise (and établissement for a SIRET) of an identifier."""
    valeur = _clean(valeur)
    if champ not in PATTERNS or not PATTERNS[champ].match(valeur):
        raise RevueApiError(422, "invalid", f"{champ.upper()} invalide : « {valeur} »")
    siren = valeur[:9]
    results = _search(valeur).get("results") or []
    # The search is full text: keep only the exact match
    entreprise = next((r for r in results if r.get("siren") == siren), None)
    if entreprise is None or not entreprise.get("nom_complet"):
        return {"trouve": False, "entreprise": None, "etablissement": None}

    siege = entreprise.get("siege") or {}
    etablissement = None
    if champ == "siret":
        matching = next(
            (
                e
                for e in [*(entreprise.get("matching_etablissements") or []), siege]
                if e.get("siret") == valeur
            ),
            None,
        )
        if matching is None:
            return {
                "trouve": False,
                "entreprise": _entreprise(entreprise, siege),
                "etablissement": None,
            }
        etablissement = _etablissement(matching, entreprise.get("nom_complet"))
    return {
        "trouve": True,
        "entreprise": _entreprise(entreprise, siege),
        "etablissement": etablissement,
    }


def _entreprise(entreprise: dict, siege: dict) -> dict:
    return {
        "siren": entreprise.get("siren") or "",
        "nom": entreprise.get("nom_complet") or "",
        "adresse": siege.get("adresse") or "",
        "activite_code": entreprise.get("activite_principale") or "",
        "etat": _etat_entreprise(entreprise.get("etat_administratif")),
    }
