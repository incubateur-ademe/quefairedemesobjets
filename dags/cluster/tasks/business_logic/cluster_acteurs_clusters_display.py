import logging

import numpy as np
import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
)
from cluster.tasks.business_logic.cluster_acteurs_read.children import (
    cluster_acteurs_read_children,
)
from cluster.tasks.business_logic.misc.df_add_original_columns import (
    df_add_original_columns,
)
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def cluster_acteurs_clusters_display(
    df: pd.DataFrame,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
    cluster_fields_separate: list[str],
    cluster_fuzzy_threshold: float,
    fields_protected: list[str],
    fields_transformed: list[str],
) -> pd.DataFrame:
    from data.models.change import (
        COL_ENTITY_TYPE,
        ENTITY_ACTEUR_DISPLAYED,
        ENTITY_ACTEUR_REVISION,
    )
    from qfdmo.models import RevisionActeur

    df_clusters = cluster_acteurs_clusters(
        df,
        cluster_fields_exact=cluster_fields_exact,
        cluster_fields_fuzzy=cluster_fields_fuzzy,
        cluster_fields_separate=cluster_fields_separate,
        cluster_fuzzy_threshold=cluster_fuzzy_threshold,
    )
    log.preview_df_as_markdown("Clusters orphelins+parents", df_clusters)

    logger.info("Ajout des colonnes de la df d'origine (ignorées par le clustering)")
    df_clusters = df_add_original_columns(df_clusters, df)
    df_clusters[COL_ENTITY_TYPE] = ENTITY_ACTEUR_DISPLAYED

    logger.info("Ajout des données calculées")
    # TODO: créer une fonction dédiée qui permet de consolider:
    # - la df de suggestions (données uniquement nécessaires aux clusters)
    # - la df de sélection (données complètes des acteurs)
    # pour pouvoir offrire en sortie de suggestion une df complète
    # qui permettre + de validation/suivis au delà de ce qui est
    # nécessaire pour le clustering lui-même
    # En attendant un quick-fix pour récupérer le statut et passer la validation
    # status_by_id = df.set_index("identifiant_unique")["statut"]
    # df_clusters["statut"] = df_clusters["identifiant_unique"].map(status_by_id)

    # Parent ID n'est pas présent dans DisplayedActeur (source des clusters)
    # donc on reconstruit ce champ à partir de RevisionActeur
    parent_ids_by_id = dict(
        RevisionActeur.objects.filter(parent__isnull=False).values_list(
            "identifiant_unique", "parent__identifiant_unique"
        )
    )
    df_clusters["parent_id"] = df_clusters["identifiant_unique"].map(
        lambda x: parent_ids_by_id.get(x, None)
    )

    logger.info("Ajout des enfants des parents existants")
    df_parents = df_clusters[df_clusters["nombre_enfants"] > 0]
    parent_to_cluster_ids = df_parents.set_index("identifiant_unique")[
        "cluster_id"
    ].to_dict()
    parent_ids = df_parents["identifiant_unique"].tolist()
    log.preview("parent_ids", parent_ids)
    df_children = cluster_acteurs_read_children(
        parent_ids=parent_ids,
        fields_to_include=fields_protected + fields_transformed + ["parent_id"],
    )
    df_children["cluster_id"] = df_children["parent_id"].map(parent_to_cluster_ids)
    df_children[COL_ENTITY_TYPE] = ENTITY_ACTEUR_REVISION

    log.preview_df_as_markdown("enfants des parents", df_children)

    df_all = pd.concat([df_clusters, df_children], ignore_index=True).replace(
        {np.nan: None}
    )

    df_all = df_sort(
        df_all,
        cluster_fields_exact=cluster_fields_exact,
        cluster_fields_fuzzy=cluster_fields_fuzzy,
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("suggestions de clusters", df_all, groupby="cluster_id")

    return df_all
