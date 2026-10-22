"""Fields edited with a select in the review screen: choices of the acteur model,
and codes of the linked objects (`*_code`: one code, `*_codes`: several, stored as
a JSON list like SuggestionSourceModel.from_acteur does). The services
(`proposition_service_codes`) are a JSON list of {action, sous_categories}."""

import json

from django.core.exceptions import FieldDoesNotExist

from data.models.suggestions.source import SuggestionSourceModel
from data.revue.errors import RevueApiError
from qfdmo.models.acteur import ActeurService, ActeurType, LabelQualite, RevisionActeur
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet

CODES = {
    "acteur_type_code": ActeurType,
    "label_codes": LabelQualite,
    "acteur_service_codes": ActeurService,
}
PROPOSITIONS = "proposition_service_codes"
# Not editable in the admin, editable in this screen
EDITABLE = {*CODES, PROPOSITIONS}


def _options(objects) -> list[dict]:
    return [{"value": o.code, "label": f"{o.libelle} ({o.code})"} for o in objects]


def champs_choix() -> dict[str, dict]:
    """{champ: {"multiple": bool, "choix": [{"value", "label"}]}}; for the services,
    `actions` are the choices of each row and `choix` its sous-catégories."""
    result = {}
    for champ in SuggestionSourceModel.model_fields:
        if champ in CODES:
            result[champ] = {
                "multiple": champ.endswith("_codes"),
                "choix": _options(CODES[champ].objects.order_by("libelle")),
            }
            continue
        try:
            field = RevisionActeur._meta.get_field(champ)
        except FieldDoesNotExist:
            continue
        if field.choices:
            result[champ] = {
                "multiple": False,
                "choix": [
                    {"value": value, "label": label or "(vide)"}
                    for value, label in field.choices
                ],
            }
    result[PROPOSITIONS] = {
        "multiple": True,
        "actions": _options(Action.objects.order_by("order")),
        "choix": _options(SousCategorieObjet.objects.order_by("libelle")),
    }
    return result


def _json_list(value: str):
    try:
        rows = json.loads(value.replace("'", '"')) if value else []
    except ValueError:
        return None
    return rows if isinstance(rows, list) else None


def _codes(champ: str, value: str) -> list[str]:
    if not champ.endswith("_codes"):
        if not value:
            raise ValueError("Valeur obligatoire")
        return [value]
    codes = _json_list(value)
    if codes is None or not all(isinstance(c, str) for c in codes):
        raise ValueError('Liste de codes attendue, ex. ["code"]')
    return codes


def _unknown(model, codes) -> list[str]:
    known = set(model.objects.filter(code__in=codes).values_list("code", flat=True))
    return sorted(set(codes) - known)


def _propositions(value: str) -> str:
    """Checks the services and writes them sorted, as from_acteur."""
    rows = _json_list(value)
    if rows is None or not all(
        isinstance(row, dict)
        and isinstance(row.get("action"), str)
        and isinstance(row.get("sous_categories"), list)
        and all(isinstance(c, str) for c in row["sous_categories"])
        for row in rows
    ):
        raise ValueError(
            'Liste attendue, ex. [{"action": "code", "sous_categories": ["code"]}]'
        )
    actions = [row["action"] for row in rows]
    errors = []
    if not all(actions):
        errors.append("Une action est obligatoire sur chaque ligne")
    if duplicates := sorted({a for a in actions if a and actions.count(a) > 1}):
        errors.append(f"Action en double : {', '.join(duplicates)}")
    if any(not row["sous_categories"] for row in rows):
        errors.append("Au moins une sous-catégorie par action")
    if unknown := _unknown(Action, [a for a in actions if a]):
        errors.append(f"Action inconnue : {', '.join(unknown)}")
    sous_categories = [c for row in rows for c in row["sous_categories"]]
    if unknown := _unknown(SousCategorieObjet, sous_categories):
        errors.append(f"Sous-catégorie inconnue : {', '.join(unknown)}")
    if errors:
        raise ValueError(*errors)
    normalized = [
        {
            "action": row["action"],
            "sous_categories": sorted(set(row["sous_categories"])),
        }
        for row in rows
    ]
    return json.dumps(
        sorted(normalized, key=lambda row: row["action"]), ensure_ascii=False
    )


def normalize_codes(valeurs: dict[str, str]) -> dict[str, str]:
    """Checks the codes (not validated by the acteur model, they would fail when
    the suggestion is applied) and writes the lists sorted, as from_acteur."""
    result = dict(valeurs)
    errors = {}
    if PROPOSITIONS in valeurs:
        try:
            result[PROPOSITIONS] = _propositions(valeurs[PROPOSITIONS])
        except ValueError as e:
            errors[PROPOSITIONS] = list(e.args)
    for champ, model in CODES.items():
        if champ not in valeurs:
            continue
        try:
            codes = _codes(champ, valeurs[champ])
        except ValueError as e:
            errors[champ] = [str(e)]
            continue
        if unknown := _unknown(model, codes):
            errors[champ] = [f"Code inconnu : {', '.join(unknown)}"]
        elif champ.endswith("_codes"):
            result[champ] = json.dumps(sorted(set(codes)), ensure_ascii=False)
    if errors:
        raise RevueApiError(422, "validation", "Valeur refusée", errors=errors)
    return result
