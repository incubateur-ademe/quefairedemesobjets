import base64
import io
import json
import logging
from collections import defaultdict
from collections.abc import Hashable, Iterable, Mapping, Sequence
from itertools import combinations
from pathlib import Path
from typing import Any, Self, TextIO

import dedupe
import duckdb
import polars as pl
from dedupe import labeler
from dedupe.api import _cleanup_scores, flatten_training

logger = logging.getLogger(__name__)
RANDOM_SEED = 42


class BusinessRulesMixin:
    """
    Mixin providing business rules logic for Dedupe models.
    Expects the host class to have `_unique_fields`, `_distinct_fields`,
    and `_index_predicates` attributes.
    """

    _unique_fields: tuple[str, ...]
    _distinct_fields: tuple[str, ...]
    _index_predicates: bool

    def score(self, pairs, data=None):
        # Let the parent score all pairs normally
        scored = super().score(pairs)

        # If no data dict provided, we can't check conflicts
        if data is None:
            return scored

        num_conflicting_pairs = 0
        # Zero out scores for conflicting pairs
        for i, pair in enumerate(scored["pairs"]):
            id_a, id_b = pair
            entity_a = data.get(id_a, {})
            entity_b = data.get(id_b, {})
            if self._has_conflict(entity_a, entity_b):
                scored["score"][i] = 0.0
                num_conflicting_pairs += 1

        logger.debug(
            "Scored %s pairs and processed %s conflict(s).",
            len(scored["pairs"]),
            num_conflicting_pairs,
        )
        return scored

    def pairs(self, data):
        """
        Override to filter out conflicting pairs BEFORE scoring.

        This prevents:
        1. Wasting compute on scoring pairs that will be rejected
        2. Transitive clustering through bridge records

        Uses DuckDB + polars Arrow integration for zero-copy in-memory blocking
        instead of sqlite3 with disk-backed tables and index creation overhead.
        """
        self.fingerprinter.index_all(data)

        # Collect fingerprints as (block_key, record_id) tuples — same format as before
        fingerprint_data = list(self.fingerprinter(data.items()))
        self.fingerprinter.reset_indices()

        if not fingerprint_data:
            return

        # Build polars DataFrame then export to Arrow for zero-copy DuckDB access.
        # No explicit schema — duckdb auto-infers types from the Arrow table,
        # supporting both string and integer record IDs as dedupe does.
        fp_df = pl.DataFrame(
            {
                "block_key": [b[0] for b in fingerprint_data],
                "record_id": [b[1] for b in fingerprint_data],
            },
        )

        con = duckdb.connect(":memory:")

        # Register as Arrow table — zero-copy from polars via pyarrow
        arrow_table = fp_df.to_arrow()
        con.register("blocking_map", arrow_table)

        # Self-join on block_key; DuckDB's columnar engine handles statistics automatically
        pairs_df = con.execute("""
            SELECT DISTINCT a.record_id AS a_record_id, b.record_id AS b_record_id
            FROM blocking_map a
            INNER JOIN blocking_map b USING (block_key)
            WHERE a.record_id < b.record_id
        """).pl()

        # Count statistics for logging — now iterating a polars DataFrame instead of SQLite cursor
        total_pairs = len(pairs_df)
        filtered_pairs = 0

        for row in pairs_df.iter_rows(named=True):
            entity_a = data[row["a_record_id"]]
            entity_b = data[row["b_record_id"]]

            # Filter out conflicting pairs BEFORE yielding them
            if self._has_conflict(entity_a, entity_b):
                filtered_pairs += 1
                continue
            yield (
                (row["a_record_id"], entity_a),
                (row["b_record_id"], entity_b),
            )

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
        self, entity_a: dict[str, object], entity_b: dict[str, object]
    ) -> bool:
        """Return True if two entities conflict on any field."""
        unique_conflicts = any(
            entity_a[field] is not None
            and entity_b[field] is not None
            and (entity_a[field] == entity_b[field])
            for field in self._unique_fields
        )

        distinct_conflicts_list = []
        for field in self._distinct_fields:
            if (entity_a[field] is None) or (entity_b[field] is None):
                distinct_conflicts_list.append(False)
                continue
            if (
                (field == "acteur_type_id")
                and ((int(entity_a[field]) == 3) and (int(entity_b[field]) == 4))
                or ((int(entity_a[field]) == 4) and (int(entity_b[field]) == 3))
            ):
                distinct_conflicts_list.append(False)
                continue
            distinct_conflicts_list.append(entity_a[field] != entity_b[field])
        distinct_conflicts = any(distinct_conflicts_list)

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
        self, clusters: Iterable, data: dict[Hashable, dict[str, object]]
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

        logger.debug("Applying business rules to clusters")
        for acteur_ids, scores in clusters:
            if len(acteur_ids) == 1:
                # Singleton case
                result.append((acteur_ids, scores))
                continue

            kept_ids, removed_ids = self._resolve_cluster(acteur_ids, scores, data)
            score_by_id = dict(zip(acteur_ids, scores))

            # le cluster nettoyé (peut être réduit à une seule entité)
            result.append((tuple(kept_ids), tuple(score_by_id[i] for i in kept_ids)))

            # chaque entité retirée redevient un singleton
            for removed_id in removed_ids:
                result.append(((removed_id,), (score_by_id[removed_id],)))

        logger.debug(
            "New clusters count after business rules applied : %s", len(result)
        )
        return result


class BusinessRulesDedupe(BusinessRulesMixin, dedupe.Dedupe):
    def __init__(
        self,
        *args,
        unique_fields: tuple[str, ...] = ("source_id",),
        distinct_fields: tuple[str, ...] = ("acteur_type_id",),
        index_predicates: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # The models can fail to converge with the default 100 iterations
        self.classifier.estimator.set_params(max_iter=1000, random_state=RANDOM_SEED)

        self._unique_fields = unique_fields
        self._distinct_fields = distinct_fields
        self._index_predicates = index_predicates

    def prepare_training(
        self,
        data: Mapping[int, Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
        training_file: TextIO | None = None,
        sample_size: int = 1500,
        blocked_proportion: float = 0.9,
    ) -> None:
        self._checkData(data)

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

    def fit(self, df_train: pl.DataFrame, entities_dict: dict) -> Self:
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

        self.train(index_predicates=self._index_predicates)
        self.cleanup_training()

        return self

    def save(self, path: str | Path | TextIO) -> None:
        settings_buffer = io.BytesIO()
        self.write_settings(settings_buffer)
        core_settings_bytes = settings_buffer.getvalue()
        core_settings_b64 = base64.b64encode(core_settings_bytes).decode("utf-8")
        full_settings = {
            "core": core_settings_b64,
            "business_rules": {
                "unique_fields": self._unique_fields,
                "distinct_fields": self._distinct_fields,
                "index_predicates": self._index_predicates,
            },
        }
        if isinstance(path, (str, Path)):
            with Path(path).open("w", encoding="utf-8") as f:
                json.dump(full_settings, f, indent=2)
        else:
            json.dump(full_settings, path, indent=2)
        logger.info("Model saved to %s", path)


class BusinessRulesStaticDedupe(BusinessRulesMixin, dedupe.StaticDedupe):
    def __init__(
        self, settings_file: str | Path | TextIO, num_cores: int | None = None
    ):
        """
        Load a model saved with BusinessRulesDedupe.save().
        """
        # 1. Load the JSON wrapper
        if hasattr(settings_file, "read"):
            full_settings = json.load(settings_file)
        else:
            with Path(settings_file).open("r", encoding="utf-8") as f:
                full_settings = json.load(f)

        # 2. Decode the core dedupe settings
        core_settings_b64 = full_settings["core"]
        core_settings_bytes = base64.b64decode(core_settings_b64)
        settings_buffer = io.BytesIO(core_settings_bytes)

        # 3. Initialize the parent StaticDedupe with the binary stream
        super().__init__(settings_buffer, num_cores=num_cores)

        # 4. Restore the business rules configuration
        business_rules = full_settings.get("business_rules", {})
        self._unique_fields = tuple(business_rules.get("unique_fields", ("source_id",)))
        self._distinct_fields = tuple(
            business_rules.get("distinct_fields", ("acteur_type_id",))
        )
        self._index_predicates = business_rules.get("index_predicates", True)
