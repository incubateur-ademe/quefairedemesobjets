import pandas as pd
from shared.tasks.business_logic import normalize
from utils.django import django_model_queryset_to_df, django_setup_full

django_setup_full()


def cluster_acteurs_read_parents(
    acteur_type_ids: list[int],
    fields: list[str],
    include_only_if_regex_matches_nom: str | None = None,
) -> pd.DataFrame:
    from qfdmo.models import ActeurType, VueActeur
    from qfdmo.models.acteur import ActeurStatus

    """Reading parents from DB (acteurs with children pointing to them)."""

    # Ajout des champs nécessaires au fonctionnement de la fonction
    # si manquant
    if "nom" not in fields:
        fields.append("nom")

    # Petite validation (on ne fait pas confiance à l'appelant)
    ids_in_db = list(ActeurType.objects.values_list("id", flat=True))
    ids_invalid = set(acteur_type_ids) - set(ids_in_db)
    if ids_invalid:
        raise ValueError(f"acteur_type_ids {ids_invalid} pas trouvés en DB")

    # On récupère les parents des acteurs types donnés
    # qui sont censés être des acteurs sans source
    parents = VueActeur.objects.prefetch_related("sources").filter(
        acteur_type__id__in=acteur_type_ids,
        statut=ActeurStatus.ACTIF,
        source_id__isnull=True,
    )

    df = django_model_queryset_to_df(parents, fields)

    # On ajoute la liste des codes des sources pour chaque acteur
    source_codes_by_parent_identifiant_unique = {
        parent.identifiant_unique: tuple(parent.sources.values_list("code", flat=True))
        for parent in parents
    }
    df["source_codes"] = df["identifiant_unique"].map(
        pd.Series(source_codes_by_parent_identifiant_unique)
    )

    # Si une regexp de nom est fournie, on l'applique
    # pour filtrer la df, sinon on garde toute la df
    if include_only_if_regex_matches_nom:
        df = df[
            df["nom"]
            # On applique la normalisation de base à la volée
            # pour simplifier les regex
            .map(normalize.string_basic).str.contains(
                include_only_if_regex_matches_nom, na=False, regex=True
            )
        ].copy()

    return df
