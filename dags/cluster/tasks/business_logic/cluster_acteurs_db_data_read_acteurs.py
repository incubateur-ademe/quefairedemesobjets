import pandas as pd
from shared.tasks.business_logic import normalize
from utils.django import (
    django_model_queryset_generate,
    django_model_queryset_to_df,
    django_model_queryset_to_sql,
    django_setup_full,
)

django_setup_full()
from qfdmo.models import DisplayedActeur  # noqa: E402


def cluster_acteurs_db_data_read_acteurs(
    include_source_ids: list[int],
    include_acteur_type_ids: list[int],
    include_only_if_regex_matches_nom: str,
    include_if_all_fields_filled: list[str],
    exclude_if_any_field_filled: list[str],
    extra_selection_fields: list[str],
) -> tuple[pd.DataFrame, str]:
    query = django_model_queryset_generate(
        DisplayedActeur, include_if_all_fields_filled, exclude_if_any_field_filled
    )
    query = query.filter(source_id__in=include_source_ids)
    query = query.filter(acteur_type_id__in=include_acteur_type_ids)

    # Un filtre en dur pour ne prendre que les acteurs actifs
    query = query.filter(statut__in=["ACTIF", "actif"])

    df = django_model_queryset_to_df(query, extra_selection_fields)

    # Si une regexp de nom est fournie, on l'applique
    # pour filtrer la df, sinon on garde toute la df
    print(f"{include_only_if_regex_matches_nom=}")
    if include_only_if_regex_matches_nom:
        df = df[
            df["nom"]
            # On applique la normalisation de base à la volée
            # pour simplifier les regex
            .map(normalize.string_basic).str.contains(
                include_only_if_regex_matches_nom, na=False, regex=True
            )
        ].copy()

    return df, django_model_queryset_to_sql(query)
