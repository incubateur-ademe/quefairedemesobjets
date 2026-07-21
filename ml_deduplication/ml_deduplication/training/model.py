import io
import logging
from collections import defaultdict
from itertools import combinations
from typing import Any, Hashable, Iterable, Mapping, Self, Sequence, TextIO

import dedupe
import dedupe.labeler as labeler
import polars as pl
from dedupe.api import _cleanup_scores, flatten_training

logger = logging.getLogger(__name__)

RANDOM_SEED = 42


class BusinessRulesDedupe(dedupe.Dedupe):
    def __init__(
        self,
        *args,
        unique_fields=("source_id",),
        distinct_fields=("acteur_type_id",),
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # The models can fail to converge with the default 100 iterations
        self.classifier.estimator.set_params(max_iter=1000, random_state=RANDOM_SEED)

        self._unique_fields = unique_fields
        self._distinct_fields = distinct_fields

    def prepare_training(
        self,
        data: Mapping[int, Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
        training_file: TextIO | None = None,
        sample_size: int = 1500,
        blocked_proportion: float = 0.9,
    ) -> None:
        self._checkData(data)

        # Reset active learner
        self.active_learner = None

        if training_file:
            self._read_training(training_file)

        # We need the active learner to know about all our
        # existing training data, so add them to data dictionary
        examples, y = flatten_training(self.training_pairs)

        self.active_learner = labeler.DedupeDisagreementLearner(
            self.data_model.predicates,
            self.data_model.distances,
            data,
            index_include=examples,
        )

        self.active_learner.matcher._classifier.set_params(
            max_iter=1000, random_state=RANDOM_SEED
        )
        self.active_learner.mark(examples, y)

    def fit(
        self,
        df_train: pl.DataFrame,
        entities_dict: dict,
        index_predicates: bool = True,
    ) -> Self:
        """
        Entraîne un objet dedupe.Dedupe à partir des paires labellisées de
        `df_train_sub`, sans passer par l'apprentissage actif interactif.

        entities contient tous les acteurs dans un dictionnaire format dedupe.
        """

        train_ids = set(df_train["identifiant_unique_i"].to_list()) | set(
            df_train["identifiant_unique_j"].to_list()
        )
        train_entities = {i: entities_dict[i] for i in train_ids}

        # Construct labeled_pairs before training
        labeled_pairs = {"match": [], "distinct": []}
        for row in df_train.iter_rows(named=True):
            pair = (
                entities_dict[row["identifiant_unique_i"]],
                entities_dict[row["identifiant_unique_j"]],
            )
            labeled_pairs["match" if row["label"] else "distinct"].append(pair)

        # Serialize labeled_pairs to a training file in memory
        training_file = io.StringIO()
        dedupe.write_training(labeled_pairs, training_file)
        training_file.seek(0)

        # use the serialized training file to avoid using mark_pairs
        # that can cause bugs depending of sample size
        self.prepare_training(
            train_entities,
            training_file=training_file,
            sample_size=max(10000, len(train_ids)),
        )

        self.train(index_predicates=index_predicates)
        self.cleanup_training()

        return self

    def score(self, pairs, data=None):
        # Let the parent score all pairs normally
        scored = super().score(pairs)

        # If no data dict provided, we can't check conflicts
        if data is None:
            return scored

        num_conflincting_pairs = 0
        # Zero out scores for conflicting pairs
        for i, pair in enumerate(scored["pairs"]):
            id_a, id_b = pair
            entity_a = data.get(id_a, {})
            entity_b = data.get(id_b, {})
            if self._has_conflict(entity_a, entity_b):
                scored["score"][i] = 0.0
                num_conflincting_pairs += 1

        logger.debug(
            "Scored %s pair and processed %s conflict(s).",
            len(scored),
            num_conflincting_pairs,
        )

        return scored

    def pairs(self, data):
        """
        Override to filter out conflicting pairs BEFORE scoring.

        This prevents:
        1. Wasting compute on scoring pairs that will be rejected
        2. Transitive clustering through bridge records
        """
        self.fingerprinter.index_all(data)

        id_type = dedupe.core.sqlite_id_type(data)

        # Blocking and pair generation are typically the first memory
        # bottlenecks, so we'll use sqlite3 to avoid doing them in memory
        import sqlite3
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            if self.in_memory:
                con = sqlite3.connect(":memory:")
            else:
                con = sqlite3.connect(temp_dir + "/blocks.db")

            # Set journal mode to WAL.
            con.execute("pragma journal_mode=off")
            con.execute(
                f"CREATE TABLE blocking_map (block_key text, record_id {id_type})"
            )
            con.executemany(
                "INSERT INTO blocking_map values (?, ?)",
                self.fingerprinter(data.items()),
            )

            self.fingerprinter.reset_indices()

            con.execute("""CREATE UNIQUE INDEX record_id_block_key_idx
                           ON blocking_map (record_id, block_key)""")
            con.execute("""CREATE INDEX block_key_idx
                           ON blocking_map (block_key)""")
            con.execute("""ANALYZE""")
            pairs = con.execute("""SELECT DISTINCT a.record_id, b.record_id
                                   FROM blocking_map a
                                   INNER JOIN blocking_map b
                                   USING (block_key)
                                   WHERE a.record_id < b.record_id""")

            # Count statistics for logging
            total_pairs = 0
            filtered_pairs = 0

            for a_record_id, b_record_id in pairs:
                total_pairs += 1
                entity_a = data[a_record_id]
                entity_b = data[b_record_id]

                # Filter out conflicting pairs BEFORE yielding them
                if self._has_conflict(entity_a, entity_b):
                    filtered_pairs += 1
                    continue

                yield (
                    (a_record_id, data[a_record_id]),
                    (b_record_id, data[b_record_id]),
                )

            pairs.close()
            con.close()

            logger.info(
                "Blocking generated %d pairs, filtered out %d conflicting pairs (%.1f%%)",
                total_pairs,
                filtered_pairs,
                (filtered_pairs / total_pairs * 100) if total_pairs > 0 else 0,
            )

    def partition(self, data, threshold=0.5):
        pairs = self.pairs(data)
        pair_scores = self.score(pairs, data)
        clusters = super().cluster(pair_scores, threshold)
        clusters = super()._add_singletons(data.keys(), clusters)
        clusters_eval = list(clusters)
        # Apply business rules at cluster level
        clusters_clean = self.apply_business_rules(clusters_eval, data)

        _cleanup_scores(pair_scores)
        return clusters_clean

    def _has_conflict(
        self,
        entity_a: dict[str, object],
        entity_b: dict[str, object],
    ) -> bool:
        """Return True if two entities conflict on any field."""
        unique_conflicts = any(
            entity_a[field] is not None
            and entity_b[field] is not None
            and (entity_a[field] == entity_b[field])
            for field in self._unique_fields
        )
        distinct_conflicts = any(
            entity_a[field] is not None
            and entity_b[field] is not None
            and (entity_a[field] != entity_b[field])
            for field in self._distinct_fields
        )

        return unique_conflicts or distinct_conflicts

    def _conflicts_in_cluster(
        self,
        cluster_ids: Sequence[Hashable],
        attributes: dict[Hashable, dict[str, object]],
    ) -> dict[Hashable, set]:
        """
        Pour chaque entité du cluster, retourne l'ensemble des autres entités
        avec lesquelles elle est en conflit (même valeur sur au moins un des
        `unique_fields`).
        """
        conflicts = defaultdict(set)
        for id_a, id_b in combinations(cluster_ids, 2):
            attrs_a, attrs_b = attributes[id_a], attributes[id_b]
            if self._has_conflict(attrs_a, attrs_b):
                conflicts[id_a].add(id_b)
                conflicts[id_b].add(id_a)
        return conflicts

    def _resolve_cluster(
        self,
        cluster_entities_ids: Sequence[Hashable],
        scores: Sequence[float],
        attributes: dict[Hashable, dict[str, object]],
    ) -> tuple[list[Hashable], list[Hashable]]:
        """
        Retire des entités d'un seul cluster jusqu'à ce qu'il respecte les
        règles métier. Retourne (ids_conservés, ids_retirés), ces derniers
        dans l'ordre où ils ont été retirés.
        """
        remaining = list(cluster_entities_ids)
        score_by_id = dict(zip(cluster_entities_ids, scores))
        removed: list[Hashable] = []

        while True:
            conflicts = self._conflicts_in_cluster(remaining, attributes)
            if not conflicts:
                break
            # on retire l'entité la plus conflictuelle ; en cas d'égalité,
            # celle dont le score de confiance dedupe est le plus faible
            worst = max(
                conflicts,
                key=lambda entity_id: (
                    len(conflicts[entity_id]),
                    -score_by_id[entity_id],
                ),
            )
            remaining.remove(worst)
            removed.append(worst)

        return remaining, removed

    def apply_business_rules(
        self,
        clusters: Iterable,
        data: dict[Hashable, dict[str, object]],
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

        logger.debug("Applying business rules to %s clusters", len(clusters))
        for acteur_ids, scores in clusters:
            if len(acteur_ids) == 1:
                # Singleton case
                result.append((acteur_ids, scores))
                continue

            kept_ids, removed_ids = self._resolve_cluster(acteur_ids, scores, data)
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

        logger.debug(
            "New clusters count after business rules applied : %s", len(result)
        )
        return result
