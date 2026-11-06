"""Parameters and selection of the places, shared by every endpoint listing them."""

import json
import math

from django.http import Http404
from ninja import Field, Schema
from pydantic import field_validator, model_validator

from qfdmo.models.acteur import DisplayedActeur


def sous_categorie_ids_for(slug: str) -> list[int]:
    """Sous-catégories of the fiche, to narrow the places to that objet.

    A fiche without sous-catégorie returns an empty list: the places are then
    not narrowed, rather than showing none.
    """
    from qfdmd.models import ProduitPage

    page = ProduitPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404(f"unknown objet: {slug}")
    return list(page.sous_categorie_objet.values_list("id", flat=True))


def clean_codes(codes: list[str]) -> list[str]:
    codes = [code.strip() for code in codes if code.strip()]
    if not codes:
        raise ValueError("geste required")
    return codes


class LieuxQuery(Schema):
    """Where and what to search: the same words as the screens' URLs.

    The position is either the visible area (`bbox`, as sent by the map) or a
    point (`longitude`, `latitude`). An unreadable bbox is refused rather than
    falling back on the point: the fallback would hide a client bug and show
    an area the user is not looking at.
    """

    # Not checked against GroupeAction, to keep a single query: an unknown
    # code yields no place.
    geste: list[str] = Field(
        ...,
        description="Code d'un GroupeAction (`/gestes`). Répétable : "
        "`?geste=reparer&geste=trier`.",
    )
    fiche: str = Field(
        "",
        description="Slug d'une fiche objet : restreint les lieux à ses "
        "sous-catégories. Inconnu : 404.",
    )
    longitude: float | None = Field(None, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)
    bbox: str | None = Field(
        None,
        description="Zone visible, JSON : "
        '`{"southWest":{"lng":…,"lat":…},"northEast":{"lng":…,"lat":…}}`. '
        "Prime sur le point.",
    )

    @field_validator("geste")
    @classmethod
    def clean_geste(cls, codes: list[str]) -> list[str]:
        return clean_codes(codes)

    @field_validator("bbox")
    @classmethod
    def clean_bbox(cls, raw: str | None) -> list[float] | None:
        """Leaflet shape to four floats: west, south, east, north."""
        if raw is None:
            return None
        try:
            corners = json.loads(raw)
            west, south, east, north = (
                float(corners[corner][axis])
                for corner in ("southWest", "northEast")
                for axis in ("lng", "lat")
            )
        except (ValueError, KeyError, TypeError):
            raise ValueError("unreadable bbox")
        for value, bound in ((west, 180), (south, 90), (east, 180), (north, 90)):
            if not math.isfinite(value) or abs(value) > bound:
                raise ValueError("bbox out of range")
        return [west, south, east, north]

    @model_validator(mode="after")
    def position_required(self):
        if self.bbox is None and None in (self.longitude, self.latitude):
            raise ValueError("bbox or longitude/latitude required")
        return self

    def queryset(self):
        """The places, through the same manager as every screen."""
        ids = sous_categorie_ids_for(self.fiche) if self.fiche else []
        acteurs = DisplayedActeur.objects.all().proposing(self.geste, ids)
        if self.bbox is not None:
            return acteurs.within(self.bbox)
        return acteurs.nearest_to(self.longitude, self.latitude)
