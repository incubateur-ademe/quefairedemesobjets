from collections import defaultdict
from itertools import combinations
from typing import Hashable, Iterable, Sequence
import logging

logger = logging.getLogger(__name__)


def _conflicts_in_cluster(
    cluster_ids: Sequence[Hashable],
    attributes: dict[Hashable, dict[str, object]],
    unique_fields: Sequence[str],
) -> dict[Hashable, set]:
    """
    Pour chaque entité du cluster, retourne l'ensemble des autres entités
    avec lesquelles elle est en conflit (même valeur sur au moins un des
    `unique_fields`).
    """
    conflicts = defaultdict(set)
    for id_a, id_b in combinations(cluster_ids, 2):
        attrs_a, attrs_b = attributes[id_a], attributes[id_b]
        if any(attrs_a[field] == attrs_b[field] for field in unique_fields):
            logger.debug("Conflict detected.")
            conflicts[id_a].add(id_b)
            conflicts[id_b].add(id_a)
    return conflicts


def _resolve_cluster(
    cluster_ids: Sequence[Hashable],
    scores: Sequence[float],
    attributes: dict[Hashable, dict[str, object]],
    unique_fields: Sequence[str],
) -> tuple[list[Hashable], list[Hashable]]:
    """
    Retire des entités d'un seul cluster jusqu'à ce qu'il respecte les
    règles métier. Retourne (ids_conservés, ids_retirés), ces derniers
    dans l'ordre où ils ont été retirés.
    """
    remaining = list(cluster_ids)
    score_by_id = dict(zip(cluster_ids, scores))
    removed: list[Hashable] = []

    while True:
        conflicts = _conflicts_in_cluster(remaining, attributes, unique_fields)
        if not conflicts:
            break
        # on retire l'entité la plus conflictuelle ; en cas d'égalité,
        # celle dont le score de confiance dedupe est le plus faible
        worst = max(
            conflicts,
            key=lambda entity_id: (len(conflicts[entity_id]), -score_by_id[entity_id]),
        )
        remaining.remove(worst)
        removed.append(worst)

    return remaining, removed


def apply_business_rules(
    partition: Iterable,
    entities_dict: dict[Hashable, dict[str, object]],
    unique_fields: Sequence[str] = ("acteur_type_id", "source_id"),
) -> list:
    """
    Applique les règles métiers à la sortie de `dedupe.partition()`.

    partition : itérable de (ids_du_cluster, scores_du_cluster), format
        exact retourné par `dedupe.partition()`.
    entities_dict : dict id -> {champ: valeur}, doit couvrir tous les ids
        présents dans `partition` et contenir les champs de `unique_fields`.
    unique_fields : champs qui doivent être uniques au sein d'un cluster.

    Retourne une nouvelle liste de clusters au même format que
    `dedupe.partition()`, où les entités retirées apparaissent en tant
    que singletons.
    """
    result: list[tuple[tuple[Hashable, ...], tuple[float, ...]]] = []

    logger.debug("Applying business rules to %s clusters", len(partition))
    for acteur_ids, scores in partition:
        if len(acteur_ids) == 1:
            # Singleton case
            result.append((acteur_ids, scores))
            continue

        kept_ids, removed_ids = _resolve_cluster(
            acteur_ids, scores, entities_dict, unique_fields
        )
        score_by_id = dict(zip(acteur_ids, scores))

        # le cluster nettoyé (peut être réduit à une seule entité)
        result.append(
            (
                tuple(kept_ids),
                tuple(score_by_id[i] for i in kept_ids),
            )
        )

        # chaque entité retirée redevient un singleton
        for removed_id in removed_ids:
            result.append(((removed_id,), (score_by_id[removed_id],)))

    return result
