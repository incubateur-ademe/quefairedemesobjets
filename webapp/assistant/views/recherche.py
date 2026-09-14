from time import perf_counter

from django.db import OperationalError, connection
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control
from modelsearch.query import Fuzzy

from assistant.objets import fiche_de
from search.models import SearchTerm

NOMBRE_DE_RESULTATS = 7
LONGUEUR_MINIMALE = 2
LONGUEUR_MAXIMALE = 100
DELAI_RECHERCHE_MS = 300


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class RechercheObjetView(View):
    """Suggestions d'objets pour la barre de recherche de l'assistant.

    Renvoie du JSON plutôt qu'un gabarit HTML : le rendu Django coûtait plus
    cher que la requête elle-même (~25 ms contre 15 ms), et le client sait
    construire sa propre liste.

    Le `statement_timeout` borne la requête plutôt que de laisser une recherche
    pathologique bloquer la saisie : mieux vaut une liste vide qu'un champ figé.
    """

    def get(self, request, *args, **kwargs):
        saisie = (request.GET.get("q") or "").strip()[:LONGUEUR_MAXIMALE]
        if len(saisie) < LONGUEUR_MINIMALE:
            return JsonResponse({"resultats": []})

        debut = perf_counter()
        resultats = self._chercher(saisie)
        duree_ms = (perf_counter() - debut) * 1000

        reponse = JsonResponse({"resultats": resultats})
        reponse.headers["Server-Timing"] = f"recherche;dur={duree_ms:.1f}"
        return reponse

    def _chercher(self, saisie: str) -> list[dict]:
        try:
            with connection.cursor() as curseur:
                curseur.execute(
                    "SET LOCAL statement_timeout = %s", [DELAI_RECHERCHE_MS]
                )

            termes = SearchTerm.objects.searchable().search(
                Fuzzy(saisie, unaccent=True)
            )[:NOMBRE_DE_RESULTATS]
            specifiques = self._specifiques([terme.id for terme in termes])

            suggestions = (
                self._suggestion(specifiques.get(terme.id)) for terme in termes
            )
            return [suggestion for suggestion in suggestions if suggestion]
        except OperationalError:
            return []

    def _specifiques(self, ids: list[int]) -> dict[int, object]:
        """Résout les sous-classes de tous les termes en trois requêtes.

        `SearchTerm.specific` interroge chaque sous-classe l'une après l'autre,
        soit jusqu'à trois requêtes par terme — 30 requêtes pour 7 résultats.
        Le même travail groupé en tient trois, quel que soit le nombre de
        suggestions.

        L'ordre de priorité reprend celui de `get_indexed_instance` : un terme
        présent dans plusieurs sous-classes est représenté par la première.
        """
        from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

        resolus: dict[int, object] = {}
        for modele in (ProduitPageSearchTerm, SearchTag, Synonyme):
            manquants = [terme_id for terme_id in ids if terme_id not in resolus]
            if not manquants:
                break
            for instance in modele.objects.filter(searchterm_ptr_id__in=manquants):
                resolus[instance.searchterm_ptr_id] = instance
        return resolus

    def _suggestion(self, specifique) -> dict | None:
        """Libellé et fiche cible d'un terme.

        `SearchTerm` est une base : seules ses sous-classes savent produire un
        titre. Sans passer par la sous-classe, tous les libellés sortent vides.

        Une suggestion sans fiche n'est pas rendue : elle mènerait à une
        impasse. C'est le cas d'un synonyme rattaché à un produit du modèle
        historique plutôt qu'à une `ProduitPage`.
        """
        if specifique is None:
            return None

        libelle = specifique.get_title()
        page = fiche_de(specifique)
        if not libelle or page is None:
            return None

        return {"libelle": libelle, "slug": page.slug}
