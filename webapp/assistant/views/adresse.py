import hashlib
import logging

import requests
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control

from qfdmo.views.autocomplete import BAN_API_URL, BAN_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

NOMBRE_DE_RESULTATS = 5
LONGUEUR_MINIMALE = 3
LONGUEUR_MAXIMALE = 200
DUREE_CACHE = 60 * 60 * 24

# Les types BAN qui désignent un point précis, par opposition à une commune.
TYPES_PRECIS = frozenset({"housenumber", "street", "locality"})


@method_decorator(
    cache_control(public=True, max_age=60 * 60, stale_while_revalidate=60 * 5),
    name="dispatch",
)
class RechercheAdresseView(View):
    """Suggestions d'adresses pour l'assistant, en proxy devant la BAN.

    Renvoie du JSON comme la recherche d'objet (ADR 0007) : le client construit
    sa liste, maîtrise l'ARIA et le clavier, et les deux champs de l'en-tête se
    comportent pareil.

    Le navigateur ne parle jamais à la BAN directement : un seul délai
    d'expiration, une seule politique de cache, et pas de couplage CORS.

    L'option « Autour de moi » de la vue historique n'est pas reprise : la
    géolocalisation est hors périmètre MVP (#3295).
    """

    def get(self, request, *args, **kwargs):
        saisie = (request.GET.get("q") or "").strip()[:LONGUEUR_MAXIMALE]
        if len(saisie) < LONGUEUR_MINIMALE:
            return JsonResponse({"resultats": []})

        # La BAN répond en ~200 ms, très au-delà du budget de 50 ms, et c'est
        # elle qui domine : le proxy n'y ajoute rien de mesurable. Les mêmes
        # adresses étant retapées sans cesse, un cache partagé ramène les
        # requêtes répétées sous la milliseconde. Le référentiel d'adresses
        # bouge lentement : 24 h est prudent.
        cle = _cle_de_cache(saisie)
        resultats = cache.get(cle)
        if resultats is None:
            resultats = self._chercher(saisie)
            # Un échec BAN renvoie une liste vide : ne pas la mémoriser, sinon
            # une panne passagère se fige pour 24 h.
            if resultats:
                cache.set(cle, resultats, DUREE_CACHE)

        return JsonResponse({"resultats": resultats})

    def _chercher(self, saisie: str) -> list[dict]:
        try:
            reponse = requests.get(
                BAN_API_URL,
                params={"q": saisie, "limit": NOMBRE_DE_RESULTATS},
                timeout=BAN_TIMEOUT_SECONDS,
            )
            reponse.raise_for_status()
            elements = (reponse.json() or {}).get("features") or []
        except (requests.RequestException, ValueError) as erreur:
            logger.warning("Proxy BAN en échec pour %r : %s", saisie, erreur)
            return []

        suggestions = (self._suggestion(element) for element in elements)
        return [suggestion for suggestion in suggestions if suggestion]

    def _suggestion(self, element: dict) -> dict | None:
        """Une suggestion, ou None si la BAN renvoie un élément inexploitable.

        `precise` distingue une adresse d'une commune : la punaise rouge ne
        s'affiche que pour la première. « Lyon » n'a pas de position à montrer
        (#3356), et son centre géographique induirait l'usager en erreur.
        """
        try:
            proprietes = element["properties"]
            longitude, latitude = element["geometry"]["coordinates"][:2]
        except (KeyError, IndexError, TypeError, ValueError):
            return None

        libelle = proprietes.get("label")
        if not libelle:
            return None

        return {
            "libelle": libelle,
            "detail": proprietes.get("context") or "",
            "longitude": longitude,
            "latitude": latitude,
            "precise": proprietes.get("type") in TYPES_PRECIS,
        }


def _cle_de_cache(saisie: str) -> str:
    """Clé stable et sans espace pour une saisie libre.

    Memcached refuse les espaces et les caractères de contrôle, qu'une adresse
    contient toujours : la saisie est donc hachée plutôt que recopiée. Le
    repli de casse regroupe « Auray » et « auray » sur la même entrée.
    """
    empreinte = hashlib.sha256(saisie.casefold().encode()).hexdigest()[:32]
    return f"assistant:adresse:{empreinte}"
