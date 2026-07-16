import io
import logging
from collections import Counter, defaultdict
from itertools import combinations
from math import comb
from typing import Any, Hashable, Iterable, Sequence

import dedupe
import numpy as np
import polars as pl
from sklearn.model_selection import train_test_split

from ml_deduplication.training.features import (
    FEATURES_NAMES_FROM_DATASET,
    DEDUPE_VARIABLE_CONFIG,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s | %(filename)s | %(message)s"
)
logger = logging.getLogger(__name__)


def create_cluster_to_acteurs_dict(features_df: pl.DataFrame) -> dict[str, set[str]]:
    """Build a dict that map cluster_ids to list of acteur_id"""
    cluster_to_acteurs_dict = defaultdict(set)

    for row in features_df.iter_rows(named=True):
        cluster_id = row["cluster_id"]
        for suffix in ["_i", "_j"]:
            if row["label"]:
                cluster_to_acteurs_dict[cluster_id].add(
                    row[f"identifiant_unique{suffix}"]
                )
            else:
                id_ = row[f"identifiant_unique{suffix}"]
                cluster_id = f"singleton__{id_}"
                cluster_to_acteurs_dict[cluster_id].add(
                    row[f"identifiant_unique{suffix}"]
                )

    return cluster_to_acteurs_dict


def create_acteur_to_cluster_dict(
    cluster_to_acteurs_dict: dict[str, set[str]],
) -> dict[str, str]:
    """Build a dict mapping acteur_id to cluster_id from a cluster_to_acteurs_dict"""
    acteur_to_cluster_id = {}

    for cluster_id, acteur_id_list in cluster_to_acteurs_dict.items():
        for acteur_id in acteur_id_list:
            acteur_to_cluster_id[acteur_id] = cluster_id

    return acteur_to_cluster_id


def build_entities_dict(
    df_features: pl.DataFrame, feature_names: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Construit un dictionnaire {id_entité: {feature: valeur, ...}} unique
    à partir des colonnes _i / _j de chaque paire.
    """
    entities = {}
    for row in df_features.iter_rows(named=True):
        for suffix, id_col in (
            ("_i", "identifiant_unique_i"),
            ("_j", "identifiant_unique_j"),
        ):
            eid = row[id_col]
            if eid not in entities:
                entity = {}
                for feature_name in feature_names:
                    value = row[f"{feature_name}{suffix}"]
                    if isinstance(value, int) or isinstance(value, float):
                        value = str(value)
                    entity[feature_name] = value
                entity["location"] = (
                    row[f"latitude{suffix}"],
                    row[f"longitude{suffix}"],
                )
                entities[eid] = entity

    return entities


def split_train_dev(
    df_train_features: pl.DataFrame,
    dev_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split df_features into train dev sets for training and hyper-parameters tuning.
    The column cluster_id_split is used in order to ensure there is no cluster data
    leaking between train and dev sets
    """
    train_cluster_ids, dev_cluster_ids = train_test_split(
        df_train_features.select("cluster_id_split").unique("cluster_id_split"),
        test_size=dev_ratio,
        random_state=seed,
    )

    df_train_sub = df_train_features.filter(
        pl.col("cluster_id_split").is_in(
            train_cluster_ids.get_column("cluster_id_split").to_list()
        )
    )

    df_dev = df_train_features.filter(
        pl.col("cluster_id_split").is_in(
            dev_cluster_ids.get_column("cluster_id_split").to_list()
        )
    )

    return df_train_sub, df_dev


def train_deduper(
    df_train: pl.DataFrame, entities_dict: dict, dedupe_variables_definition: list
) -> dedupe.Dedupe:
    """
    Entraîne un objet dedupe.Dedupe à partir des paires labellisées de
    `df_train_sub`, sans passer par l'apprentissage actif interactif.

    entities contient tous les acteurs dans un dictionnaire format dedupe.
    """
    deduper = dedupe.Dedupe(dedupe_variables_definition)

    # Increase max iter of the logistic regression classifier
    deduper.classifier.estimator.set_params(max_iter=1000)

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
    deduper.prepare_training(
        train_entities,
        training_file=training_file,
        sample_size=max(10000, len(train_ids)),
    )

    deduper.train()
    deduper.cleanup_training()

    return deduper


def pairwise_metrics_from_clusters(true_clusters: dict, pred_clusters: dict) -> dict:
    """
    Precision / recall / F1 au niveau paire, calculés de façon EXHAUSTIVE
    sur toutes les paires possibles entre les entités considérées (et pas
    seulement sur les paires présentes dans `pairs_df`).

    En effet, `deduper.partition()` regroupe les entités en clusters : deux
    entités peuvent se retrouver dans le même cluster prédit sans avoir
    jamais formé une paire annotée dans le dataframe de base. Ignorer ces
    paires "nouvelles" revient à ne jamais compter certains faux positifs
    (ni certains faux négatifs pour des paires vraies non couvertes par
    l'échantillon), ce qui biaise la métrique à la hausse.

    On évite d'énumérer explicitement les O(n²) paires en s'appuyant sur
    une formule combinatoire à partir des tailles de clusters (vrais,
    prédits, et intersections vrai×prédit) : pour un groupe de taille n,
    il y a C(n,2) paires internes.

    `true_clusters` et `pred_clusters` doivent couvrir exactement le même
    ensemble d'identifiants (typiquement : toutes les entités du split
    évalué pour lesquelles la vérité terrain est connue).
    """
    ids = list(true_clusters.keys())
    assert set(ids) == set(
        pred_clusters.keys()
    ), "true_clusters et pred_clusters doivent couvrir les mêmes ids"

    # nb de paires prédites comme duplicats = somme des C(taille,2) par cluster prédit
    pred_sizes = Counter(pred_clusters[i] for i in ids)
    predicted_positive = sum(comb(n, 2) for n in pred_sizes.values())

    # nb de paires réellement duplicats = somme des C(taille,2) par cluster vrai
    true_sizes = Counter(true_clusters[i] for i in ids)
    actual_positive = sum(comb(n, 2) for n in true_sizes.values())

    # vrais positifs = paires qui sont ensemble à la fois dans le cluster prédit
    # ET le cluster vrai
    joint_sizes = Counter((pred_clusters[i], true_clusters[i]) for i in ids)
    tp = sum(comb(n, 2) for n in joint_sizes.values())

    fp = predicted_positive - tp
    fn = actual_positive - tp

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def partition_to_dict(dedupe_partitions, all_ids: set) -> dict:
    """
    Convertit la sortie de `deduper.partition()` en dict {id: cluster_id}.
    les cluster_id sont générés automatiquement.
    Les entités que dedupe n'a rattachées à aucun cluster (cas limite selon
    versions) sont explicitement placées dans un cluster singleton.
    """
    id_to_cluster = {}
    for cluster_idx, (ids, _scores) in enumerate(dedupe_partitions):
        for eid in ids:
            id_to_cluster[eid] = f"c_{cluster_idx}"

    # Ce cas ne devrait pas arriver sur les dernières versions
    for eid in all_ids:
        default_cluster_id = f"singleton_{eid}"
        returned_value = id_to_cluster.setdefault(eid, default_cluster_id)
        if returned_value == default_cluster_id:
            logger.debug(
                "Inserted {} as singleton that was not present in the pred dict",
                default_cluster_id,
            )

    return id_to_cluster


def fbeta(precision: float, recall: float, beta: float = 0.5) -> float:
    """F-bêta : beta < 1 favorise la précision par rapport au rappel."""
    if precision == 0 and recall == 0:
        return 0.0
    b2 = beta**2
    return (1 + b2) * precision * recall / (b2 * precision + recall)


def select_best_threshold(
    deduper: dedupe.Dedupe,
    entities_dev: dict,
    id_to_cluster_id_dev: dict,
    thresholds=np.arange(0.10, 1.00, 0.05),
    min_recall: float = 0.3,
) -> tuple[float, dict]:
    """
    Teste une grille de seuils sur le jeu de dev et choisit celui qui :
      - maximise la précision, parmi les seuils qui respectent un rappel
        minimal (`min_recall`) ;
      - à défaut (aucun seuil ne respecte le rappel minimal), maximise le
        F-bêta (bêta=0.5, qui pondère davantage la précision).

    La précision/rappel est calculée de façon EXHAUSTIVE sur toutes les
    entités du dev ayant une vérité terrain connue (via `clusters_df`),
    et non sur le seul sous-échantillon de paires annotées : cela évite
    d'ignorer les faux positifs "inventés" par le clustering de dedupe.

    NB : on relance `partition()` pour chaque seuil (simplification). Sur
    un très gros volume, on pourrait factoriser le blocking/scoring et ne
    faire varier que l'étape de clustering.
    """
    eval_ids = set(id_to_cluster_id_dev.keys())

    results = []
    for t in thresholds:
        # On demande à dedupe de clusteriser et on obtient une
        # liste de liste d'ids regroupés
        partition_pred = deduper.partition(entities_dev, float(t))

        # On crée un dict entity_id -> cluster_id + singleton
        id_to_cluster_pred = partition_to_dict(partition_pred, set(entities_dev.keys()))
        # On s'assure qu'il n'y ait que des ids du jeu d'évaluation
        id_to_cluster_pred = {i: id_to_cluster_pred[i] for i in eval_ids}

        # On calcule les métriques en comparant
        metrics = pairwise_metrics_from_clusters(
            id_to_cluster_id_dev, id_to_cluster_pred
        )
        results.append((float(t), metrics))
        print(
            f"  seuil={t:.2f}  precision={metrics['precision']:.3f}  "
            f"recall={metrics['recall']:.3f}  f1={metrics['f1']:.3f}"
        )
        print("-----")

    # 1) parmi les seuils respectant le rappel minimal, on prend le plus précis
    eligibles = [(t, m) for t, m in results if m["recall"] >= min_recall]
    if eligibles:
        return max(eligibles, key=lambda x: x[1]["precision"])

    # 2) sinon, repli sur le F-bêta (favorise quand même la précision)
    return max(
        results, key=lambda x: fbeta(x[1]["precision"], x[1]["recall"], beta=0.5)
    )


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


def run_pipeline(df_features: pl.DataFrame):
    # Create cluster to ids dict
    cluster_to_acteur_dict = create_cluster_to_acteurs_dict(df_features)

    # Create id to cluster dict
    acteur_to_cluster_id_dict = create_acteur_to_cluster_dict(cluster_to_acteur_dict)

    # select features
    features_names = FEATURES_NAMES_FROM_DATASET
    # Create entities dict
    entities_dict = build_entities_dict(df_features, feature_names=features_names)

    # split train into train/dev
    df_train, df_dev = split_train_dev(df_features.filter(pl.col("split") == "train"))

    # config variables
    dedupe_variable_config = DEDUPE_VARIABLE_CONFIG

    # train dedupe
    logger.info("Starting dedupe training")
    deduper = train_deduper(df_train, entities_dict, dedupe_variable_config)
    logger.info("Finished dedupe training")

    # select threshold on dev
    logger.info("Starting best threshold selection....")
    entities_ids_dev = set(df_dev["identifiant_unique_i"].to_list()) | set(
        df_dev["identifiant_unique_j"].to_list()
    )
    entities_dict_dev = {
        k: v for k, v in entities_dict.items() if k in entities_ids_dev
    }
    id_to_cluster_id_dict_dev = {
        k: v for k, v in acteur_to_cluster_id_dict.items() if k in entities_ids_dev
    }
    best_threshold, best_metrics = select_best_threshold(
        deduper=deduper,
        entities_dev=entities_dict_dev,
        id_to_cluster_id_dev=id_to_cluster_id_dict_dev,
    )
    logger.info(
        "Best threshold found: %s, best metrics: %s", best_threshold, best_metrics
    )

    # train on full train
    logger.info("Starting dedupe training on full training set")
    deduper = train_deduper(
        df_features.filter(pl.col("split") == "train"),
        entities_dict,
        dedupe_variable_config,
    )
    logger.info("Finished dedupe training on full training set")

    # evaluate on test with best threshold
    logger.info("Starting predicting on test set")
    df_test = df_features.filter(pl.col("split") == "test")
    entities_ids_test = set(df_test["identifiant_unique_i"].to_list()) | set(
        df_test["identifiant_unique_j"].to_list()
    )
    entities_dict_test = {
        k: v for k, v in entities_dict.items() if k in entities_ids_test
    }
    id_to_cluster_id_dict_test = {
        k: v for k, v in acteur_to_cluster_id_dict.items() if k in entities_ids_test
    }
    partition_test = deduper.partition(
        data=entities_dict_test, threshold=best_threshold
    )  # type: ignore
    id_to_cluster_test_pred = partition_to_dict(
        partition_test, set(entities_dict_test.keys())
    )
    metrics = pairwise_metrics_from_clusters(
        id_to_cluster_id_dict_test, id_to_cluster_test_pred
    )
    logger.info("Test metrics before applying business rules: %s", metrics)

    # Apply business rules
    logger.info("Applying business rules")
    partition_test_cleaned = apply_business_rules(partition_test, entities_dict_test)
    id_to_cluster_test_pred_cleaned = partition_to_dict(
        partition_test_cleaned, set(entities_dict_test.keys())
    )
    metrics = pairwise_metrics_from_clusters(
        id_to_cluster_id_dict_test, id_to_cluster_test_pred_cleaned
    )
    logger.info("Test metrics after applying business rules: %s", metrics)


if __name__ == "__main__":
    df_features = pl.read_parquet(
        "/Users/luis/projets/beta.gouv/qfdmod/quefairedemesobjets/data-platform/notebooks/deduplication/datasets/features_dataset_20260715.parquet"
    )
    run_pipeline(df_features)
