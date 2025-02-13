import pandas as pd
from cluster.tasks.business_logic.misc.df_metadata_get import df_metadata_get
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_suggestions_to_db(
    df_clusters: pd.DataFrame,
    identifiant_action: str,
    identifiant_execution: str,
) -> None:

    from data.models import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )
    from data.models.change import (
        COL_CHANGE_ORDER,
        COL_CHANGE_REASON,
        COL_CHANGE_TYPE,
        COL_ENTITY_TYPE,
    )

    """Ecriture des suggestions de clusters en base de données

    Args:
        df_clusters (pd.DataFrame): clusters à écrire en base
        identifiant_action (str): ex: dag_id pour Airflow
        identifiant_execution (str): ex: run_id pour Airflow
    """
    # Raccourci pour la seule df qu'on utilise
    df = df_clusters

    cohorte = SuggestionCohorte(
        # id: ce champ est auto-généré
        identifiant_action=identifiant_action,
        identifiant_execution=identifiant_execution,
        type_action=SuggestionAction.CLUSTERING,
        statut=SuggestionStatut.AVALIDER,
        metadata=df_metadata_get(df),
    )
    cohorte.save()

    cols_changes = [
        COL_CHANGE_ORDER,
        COL_ENTITY_TYPE,
        "identifiant_unique",
        COL_CHANGE_TYPE,
        COL_CHANGE_REASON,
    ]

    for cluster_id in df["cluster_id"].unique():
        cluster = df[df["cluster_id"] == cluster_id].copy()
        suggestion = Suggestion(
            suggestion_cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            contexte=cluster.to_dict(orient="records"),
            suggestion={
                "cluster_id": cluster_id,
                "changes": cluster[cols_changes].to_dict(orient="records"),
            },
        )
        suggestion.save()
