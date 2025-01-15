import numpy as np
import pandas as pd
from shared.tasks.business_logic import normalize
from utils.django import (
    django_model_queryset_generate,
    django_model_queryset_to_df,
    django_model_queryset_to_sql,
    django_setup_full,
)

django_setup_full()
from django.db.models import Model  # noqa: E402

from qfdmo.models import ActeurType, Source  # noqa: E402
from qfdmo.models.acteur import ActeurStatus  # noqa: E402


def cluster_acteurs_db_data_read_acteurs(
    model_class: type[Model],
    include_source_ids: list[int],
    include_acteur_type_ids: list[int],
    include_only_if_regex_matches_nom: str,
    include_if_all_fields_filled: list[str],
    exclude_if_any_field_filled: list[str],
    extra_dataframe_fields: list[str],
) -> tuple[pd.DataFrame, str]:
    """Lire les données des acteurs depuis la DB et retourner un DataFrame
    (+ requête SQL pour débug)

    Sachant qu'on travaille potentiellement avec des propriétés dérivées (ex: @property)
    qui n'existent pas en DB, le queryset de Django ne peut pas gérer ces propriétés.

    Donc on fait 2 étapes:
    1) Django queryset: où on essaye au mieux de filtrer les données en amont
    2) DataFrame: où on ajoute toute la logique non gérée par Django query (@property,
    filtres plus complexes, etc.)
        bonus debug: on rajoute les codes sources/types

    🟠 Concernant les exceptions:
     - oui ce n'est pas une erreurs en soit de ne pas récupérer de données acteurs
        (c'est peut être la réalité métier)
     - en revanche les pipelines Airflow deviennent complexes avec le risque si
        une tâche échoue de ne pas savoir pourquoi, d'avoir les tâches suivantes
        qui s'exécutent pour rien, d'avoir des effets de bord, etc.
     - en plus de cela: tester les pipelines Airflow de bout en bout n'est pas facile
     => donc on préfère simplifier l'approche en soulevant des exceptions dès
        que possible via cette fonction

    Args:
        model_class (type[Model]): Le modèle Django à lire, le mettre en paramètre
            nous permet de choisir Acteur, RevisionActeur ou DisplayedActeur

        ➕ include_source_ids (list[int]): Les sources à inclure

        ➕ include_acteur_type_ids (list[int]): Les types d'acteurs à inclure

        ➕ include_only_if_regex_matches_nom (str): acteurs inclus si nom match
            SI pas de regex = pas de filtrage = tous les noms sont inclus

        ➕ include_if_all_fields_filled (list[str]): acteurs inclus
            SI TOUS les champs remplis

        ❌ exclude_if_any_field_filled (list[str]): acteurs exclus
            SI N'IMPORTE QUEL champ rempli

        📦 extra_dataframe_fields (list[str]): Les champs à rajouter à la df finale
            MEME si pas utils à la sélection (parce qu'on en a besoin plus
            tard comme pour l'ago de clustering)

    Returns:
        tuple[pd.DataFrame, str]: Le DataFrame des acteurs et la requête SQL utilisée
    """

    # -----------------------------------
    # 1) Etape Django queryset
    # -----------------------------------
    # Pour limiter au maximum les données à lire en DB
    query = django_model_queryset_generate(
        model_class, include_if_all_fields_filled, exclude_if_any_field_filled
    )
    query = query.filter(source_id__in=include_source_ids)
    query = query.filter(acteur_type_id__in=include_acteur_type_ids)

    # Un filtre en dur pour ne prendre que les acteurs actifs
    query = query.filter(statut=ActeurStatus.ACTIF)

    fields = ["identifiant_unique", "statut", "source_id", "acteur_type_id", "nom"]
    fields += include_if_all_fields_filled
    fields += exclude_if_any_field_filled
    fields += extra_dataframe_fields

    # -----------------------------------
    # 2) Etape DataFrame
    # -----------------------------------
    # Pour appliquer les traitements non gérés en étape 1 (ex: @property)
    df = django_model_queryset_to_df(query, fields)

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

    # Conséquence de tolérer des chaines vides en base: on converti tout le
    # vide en None pour simplifier l'inclusion/exclusion qui suit
    df = df.replace({"": None, np.nan: None})

    # On ne garde que les lignes où TOUS les champs sont remplis
    df = df[df[include_if_all_fields_filled].notna().all(axis=1)].copy()

    # On exclude les lignes où N'IMPORTE QUEL champ est rempli
    df = df[~df[exclude_if_any_field_filled].notna().any(axis=1)].copy()

    if df.empty:
        raise ValueError("Dataframe vide après filtrage")

    # -----------------------------------
    # Bonus debug
    # -----------------------------------
    # Ajout des codes sources et types d'acteurs puisqu'ils sont
    # directements liés au filtrage, et débugger une pipeline
    # avec des IDs uniquement est très compliqué
    mapping_source_codes_by_ids = {x.id: x.code for x in Source.objects.all()}
    mapping_acteur_type_codes_by_ids = {x.id: x.code for x in ActeurType.objects.all()}
    df["source_code"] = df["source_id"].map(mapping_source_codes_by_ids)
    df["acteur_type_code"] = df["acteur_type_id"].map(mapping_acteur_type_codes_by_ids)

    return df, django_model_queryset_to_sql(query)
