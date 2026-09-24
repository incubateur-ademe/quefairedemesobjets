"""The user's search context, carried by the URL.

The objet and the address follow the user from the home page to the fiche,
then to the solutions and to a lieu's detail. Carrying them in the URL rather
than in the session makes every screen shareable and reloadable, and avoids
server state to invalidate.
"""

import math
from dataclasses import dataclass

PARAMS = ("fiche", "objet", "adresse", "longitude", "latitude", "precise")


@dataclass(frozen=True)
class Parcours:
    """What the user typed, as it travels from one screen to the next.

    `fiche` is the slug of the targeted `ProduitPage`, set by the autocomplete
    or inferred from the label; `objet` is the label itself, shown again in
    the search field. Both travel: the slug is what the server searches on,
    the label is what the user recognises.
    """

    fiche: str = ""
    objet: str = ""
    adresse: str = ""
    longitude: float | None = None
    latitude: float | None = None
    precise: bool = False

    @classmethod
    def from_query(cls, params) -> "Parcours":
        """Reads the parcours from a `request.GET`, tolerating absence and noise.

        An unreadable coordinate is treated as absent rather than as an error:
        the user typed an address, it is the suggestion that was not chosen.
        The map knows how to land on its feet.
        """
        return cls(
            fiche=(params.get("fiche") or "").strip(),
            objet=(params.get("objet") or "").strip(),
            adresse=(params.get("adresse") or "").strip(),
            longitude=_to_float(params.get("longitude")),
            latitude=_to_float(params.get("latitude")),
            precise=params.get("precise") in ("true", "True", "1"),
        )

    @property
    def is_located(self) -> bool:
        """True if a usable position comes with the address."""
        return self.longitude is not None and self.latitude is not None

    def as_params(self) -> dict[str, str]:
        """The parcours as URL parameters, without the empty values."""
        values = {
            "fiche": self.fiche,
            "objet": self.objet,
            "adresse": self.adresse,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "precise": "true" if self.precise else "",
        }
        # `is not None`, not truthiness: a longitude of exactly 0.0 is a real
        # position (the Greenwich meridian crosses Normandy).
        return {
            key: str(value) for key, value in values.items() if value not in (None, "")
        }


def _to_float(value) -> float | None:
    """A finite float, or None: `float("nan")` parses, but is no position."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
