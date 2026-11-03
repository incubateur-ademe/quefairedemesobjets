"""API v1 endpoints of the assistant's search fields."""

from ninja import Router, Schema
from ninja.decorators import decorate_view

from assistant.adresses import suggest_adresses
from assistant.objets import suggest_objets
from core.http_cache import CACHE_FIVE_MINUTES, CACHE_ONE_HOUR

router = Router()


class SuggestionObjet(Schema):
    label: str
    slug: str


class SuggestionAdresse(Schema):
    label: str
    detail: str
    longitude: float
    latitude: float
    precise: bool


class SuggestionsObjets(Schema):
    results: list[SuggestionObjet]


class SuggestionsAdresses(Schema):
    results: list[SuggestionAdresse]


@router.get(
    "/objets",
    response=SuggestionsObjets,
    url_name="objets",
    summary="Suggestions d'objets pour une saisie",
)
@decorate_view(CACHE_FIVE_MINUTES)
def objets(request, q: str = ""):
    """Sept suggestions au plus, dès deux caractères. `slug` désigne la fiche."""
    return {"results": suggest_objets(q)}


@router.get(
    "/adresses",
    response=SuggestionsAdresses,
    url_name="adresses",
    summary="Suggestions d'adresses pour une saisie",
)
@decorate_view(CACHE_ONE_HOUR)
def adresses(request, q: str = ""):
    """Cinq suggestions au plus, dès trois caractères, via la Base Adresse
    Nationale. `precise` distingue une adresse d'une commune."""
    return {"results": suggest_adresses(q)}
