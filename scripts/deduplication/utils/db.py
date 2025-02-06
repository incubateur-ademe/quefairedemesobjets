"""Utilitaires pour les interactions DB"""

from functools import cache

from qfdmo.models.acteur import Source


# A propos de @cache:
# Données de très petite taille donc unbounded cache est OK
# Raison pour le cache:
# - pouvoir utiliser le mapping dans des sous-tâches sans
#    avoir à se trimballer des arguments partout
#   (manage cluster -> manage parent)
# - gain de performance: au 2024-12-18 il nous faut 2h23min pour
#    traiter n=4700 clusters, preuve que l'accès DB est assez lent
#    et donc économiser n=requêtes (mapping utilisé à la fois dans
#    db_manage_cluster et db_manage_parent) ne parait pas scandaleux
@cache
def db_source_ids_by_code_get() -> dict:
    """Récupération de la liste des sources par code pour les utiliser
    dans la logique de priorisation des sources pour la fusion des données

    Returns:
        result: dict de sources code:id
    """
    return dict(Source.objects.values_list("code", "id"))
