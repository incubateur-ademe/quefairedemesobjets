import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_metadata import (
    cluster_acteurs_metadata,
)
from utils.django import django_setup_full

django_setup_full()

from data.models import Suggestion, SuggestionCohorte, SuggestionStatut  # noqa: E402


def cluster_acteur_suggestions_to_db(
    df_clusters: pd.DataFrame,
    identifiant_action: str,
    identifiant_execution: str,
) -> None:
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
        # TODO: déplacer "type_action" dans Suggestion
        # Je pense que fixer un type d'action au niveau
        # du cohorte est trop restrictif: par exemple dans
        # le cade du clustering, on va pouvoir proposer
        # des clusters nouveaux ET des clusters à fusionner
        # type_action
        statut=SuggestionStatut.AVALIDER,
        metadata=cluster_acteurs_metadata(df),
    )
    cohorte.save()
    for _, cluster in df.iterrows():
        suggestion = Suggestion(
            cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            context=cluster.to_dict(),
            suggestion=cluster[["cluster_id", "identifiant_unique"]].to_dict(),
        )
        suggestion.save()
