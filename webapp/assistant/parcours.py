"""Contexte de recherche de l'usager, transporté par l'URL.

L'objet et l'adresse suivent l'usager de l'accueil à la fiche, puis aux
solutions et au détail d'un lieu. Les porter dans l'URL plutôt qu'en session
rend chaque écran partageable et rechargeable, et évite un état serveur à
invalider.
"""

from dataclasses import dataclass

PARAMETRES = ("objet", "adresse", "longitude", "latitude", "precise")


@dataclass(frozen=True)
class Parcours:
    """Ce que l'usager a saisi, tel qu'il voyage d'un écran à l'autre."""

    objet: str = ""
    adresse: str = ""
    longitude: float | None = None
    latitude: float | None = None
    precise: bool = False

    @classmethod
    def depuis(cls, parametres) -> "Parcours":
        """Lit le parcours d'un `request.GET`, en tolérant l'absence ou le bruit.

        Une coordonnée illisible est traitée comme absente plutôt que comme une
        erreur : l'usager a saisi une adresse, c'est la suggestion qui n'a pas
        été choisie. La carte saura retomber sur ses pieds.
        """
        return cls(
            objet=(parametres.get("objet") or "").strip(),
            adresse=(parametres.get("adresse") or "").strip(),
            longitude=_flottant(parametres.get("longitude")),
            latitude=_flottant(parametres.get("latitude")),
            precise=parametres.get("precise") in ("true", "True", "1"),
        )

    @property
    def localise(self) -> bool:
        """Vrai si une position exploitable accompagne l'adresse."""
        return self.longitude is not None and self.latitude is not None

    def en_parametres(self) -> dict[str, str]:
        """Le parcours sous forme de paramètres d'URL, sans les valeurs vides."""
        valeurs = {
            "objet": self.objet,
            "adresse": self.adresse,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "precise": "true" if self.precise else "",
        }
        return {cle: str(valeur) for cle, valeur in valeurs.items() if valeur}


def _flottant(valeur) -> float | None:
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None
