"""The user's search, carried from screen to screen by the URL: every screen
stays shareable and reloadable."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Parcours:
    """`fiche`: slug of the `ProduitPage`; `objet`: the label shown in the
    search field; `synonyme`: slug of the synonyme chosen, if any."""

    fiche: str = ""
    objet: str = ""
    synonyme: str = ""
    adresse: str = ""
    longitude: float | None = None
    latitude: float | None = None
    precise: bool = False

    @classmethod
    def from_query(cls, params) -> "Parcours":
        """Reads a `request.GET`; an unreadable coordinate counts as absent."""
        return cls(
            fiche=(params.get("fiche") or "").strip(),
            objet=(params.get("objet") or "").strip(),
            synonyme=(params.get("synonyme") or "").strip(),
            adresse=(params.get("adresse") or "").strip(),
            longitude=_to_float(params.get("longitude")),
            latitude=_to_float(params.get("latitude")),
            precise=params.get("precise") in ("true", "True", "1"),
        )

    @property
    def is_located(self) -> bool:
        return self.longitude is not None and self.latitude is not None

    def as_params(self) -> dict[str, str]:
        """The parcours as URL parameters, without the empty values."""
        values = {
            "fiche": self.fiche,
            "objet": self.objet,
            "synonyme": self.synonyme,
            "adresse": self.adresse,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "precise": "true" if self.precise else "",
        }
        # Not truthiness: a longitude of 0.0 is a position.
        return {
            key: str(value) for key, value in values.items() if value not in (None, "")
        }


def _to_float(value) -> float | None:
    """A finite float, or None: `float("nan")` parses too."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
