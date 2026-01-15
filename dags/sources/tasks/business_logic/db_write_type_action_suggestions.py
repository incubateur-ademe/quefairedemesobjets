import json
import logging
from datetime import datetime

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from utils.django import django_setup_full

django_setup_full()


logger = logging.getLogger(__name__)


def _build_suggestion_logs(
    *,
    df_log_error: pd.DataFrame,
    df_log_warning: pd.DataFrame,
    df_acteur_to_create: pd.DataFrame,
    df_acteur_to_update: pd.DataFrame,
    df_acteur_to_delete: pd.DataFrame,
    metadata_to_create: dict,
    metadata_to_update: dict,
    metadata_to_delete: dict,
):
    # get df_log_error and df_log_warning intersection with df_acteur_to_create
    df_log_error_to_create = df_log_error[
        df_log_error["identifiant_unique"].isin(
            df_acteur_to_create["identifiant_unique"]
        )
    ]
    df_log_warning_to_create = df_log_warning[
        df_log_warning["identifiant_unique"].isin(
            df_acteur_to_create["identifiant_unique"]
        )
    ]

    # get df_log_error and df_log_warning intersection with df_acteur_to_update
    df_log_error_to_update = df_log_error[
        df_log_error["identifiant_unique"].isin(
            df_acteur_to_update["identifiant_unique"]
        )
    ]
    df_log_warning_to_update = df_log_warning[
        df_log_warning["identifiant_unique"].isin(
            df_acteur_to_update["identifiant_unique"]
        )
    ]

    # get df_log_error and df_log_warning without intersection with df_acteur_to_create
    # and df_acteur_to_update
    df_log_error_left_over = df_log_error[
        ~df_log_error["identifiant_unique"].isin(
            df_acteur_to_create["identifiant_unique"]
        )
        & ~df_log_error["identifiant_unique"].isin(
            df_acteur_to_update["identifiant_unique"]
        )
        & ~df_log_error["identifiant_unique"].isin(
            df_acteur_to_delete["identifiant_unique"]
        )
    ]
    df_log_warning_left_over = df_log_warning[
        ~df_log_warning["identifiant_unique"].isin(
            df_acteur_to_create["identifiant_unique"]
        )
        & ~df_log_warning["identifiant_unique"].isin(
            df_acteur_to_update["identifiant_unique"]
        )
        & ~df_log_warning["identifiant_unique"].isin(
            df_acteur_to_delete["identifiant_unique"]
        )
    ]

    if nb_lines_ignorees := len(df_log_error_left_over):
        metadata_to_create["nombre de lignes non-traitees à cause d'erreurs"] = (
            nb_lines_ignorees
        )
        df_log_error_to_create = pd.concat(
            [df_log_error_to_create, df_log_error_left_over]
        )
    if not df_log_error_to_create.empty:
        metadata_to_create["nombre de lignes non-traitees à cause d'erreurs"] = len(
            df_log_error_to_create
        )
    if not df_log_warning_to_create.empty:
        metadata_to_create["nombre de valeurs de champs ignorées"] = len(
            df_log_warning_to_create
        )

    if nb_lines_data_ignorees := len(df_log_warning_to_update):
        metadata_to_update[
            "nombre de modifications de champs ignorées parmis les acteurs à mettre à"
            " jour"
        ] = nb_lines_data_ignorees
    if nb_lines_log_warning_left_over := len(df_log_warning_left_over):
        metadata_to_update[
            "nombre de modifications de champs ignorées parmis les acteurs non modifiés"
        ] = nb_lines_log_warning_left_over
    df_log_warning_to_update = pd.concat(
        [df_log_warning_to_update, df_log_warning_left_over]
    )

    return (
        df_log_error_to_create,
        df_log_warning_to_create,
        df_log_error_to_update,
        df_log_warning_to_update,
        metadata_to_create,
        metadata_to_update,
        metadata_to_delete,
    )


def db_write_type_action_suggestions(
    dag_name: str,
    run_id: str,
    df_acteur_to_create: pd.DataFrame,
    df_acteur_to_delete: pd.DataFrame,
    df_acteur_to_update: pd.DataFrame,
    metadata_to_create: dict,
    metadata_to_update: dict,
    metadata_to_delete: dict,
    df_log_error: pd.DataFrame,
    df_log_warning: pd.DataFrame,
    use_legacy_suggestions: bool,
):

    (
        df_log_error_to_create,
        df_log_warning_to_create,
        df_log_error_to_update,
        df_log_warning_to_update,
        metadata_to_create,
        metadata_to_update,
        metadata_to_delete,
    ) = _build_suggestion_logs(
        df_log_error=df_log_error,
        df_log_warning=df_log_warning,
        df_acteur_to_create=df_acteur_to_create,
        df_acteur_to_update=df_acteur_to_update,
        df_acteur_to_delete=df_acteur_to_delete,
        metadata_to_create=metadata_to_create,
        metadata_to_update=metadata_to_update,
        metadata_to_delete=metadata_to_delete,
    )

    run_name = run_id.replace("__", " - ")

    if use_legacy_suggestions:
        function_to_use = insert_suggestion_legacy
    else:
        function_to_use = insert_suggestion

    function_to_use(
        df=df_acteur_to_create,
        metadata=metadata_to_create,
        dag_name=f"{dag_name} - AJOUT",
        run_name=run_name,
        type_action=constants.SUGGESTION_SOURCE_AJOUT,
        df_log_error=df_log_error_to_create,
        df_log_warning=df_log_warning_to_create,
    )
    function_to_use(
        df=df_acteur_to_delete,
        metadata=metadata_to_delete,
        dag_name=f"{dag_name} - SUP",
        run_name=run_name,
        type_action=constants.SUGGESTION_SOURCE_SUPRESSION,
    )
    function_to_use(
        df=df_acteur_to_update,
        metadata=metadata_to_update,
        dag_name=f"{dag_name} - MODIF",
        run_name=run_name,
        type_action=constants.SUGGESTION_SOURCE_MODIFICATION,
        df_log_error=df_log_error_to_update,
        df_log_warning=df_log_warning_to_update,
    )


def insert_suggestion(
    df: pd.DataFrame,
    metadata: dict,
    dag_name: str,
    run_name: str,
    type_action: str,
    df_log_error: pd.DataFrame = pd.DataFrame(),
    df_log_warning: pd.DataFrame = pd.DataFrame(),
):
    from data.models.suggestion import (
        SuggestionCohorte,
        SuggestionGroupe,
        SuggestionLog,
        SuggestionUnitaire,
    )
    from data.models.suggestions.source import SuggestionSourceModel
    from qfdmo.models.acteur import Acteur, RevisionActeur

    if df.empty:
        return

    # Create a new cohorte
    suggestion_cohorte = SuggestionCohorte(
        identifiant_action=dag_name,
        identifiant_execution=run_name,
        type_action=type_action,
        statut=constants.SUGGESTION_AVALIDER,
        metadata=metadata,
    )
    suggestion_cohorte.save()

    # Insert suggestion_logs
    if not df_log_error.empty:
        for index, row in df_log_error.iterrows():
            SuggestionLog(
                suggestion_cohorte=suggestion_cohorte,
                niveau_de_log=SuggestionLog.SuggestionLogLevel.ERROR,
                fonction_de_transformation=row["fonction_de_transformation"],
                origine_colonnes=row["origine_colonnes"],
                origine_valeurs=row["origine_valeurs"],
                destination_colonnes=row["destination_colonnes"],
                message=row["message"],
            ).save()
    if not df_log_warning.empty:
        for index, row in df_log_warning.iterrows():
            SuggestionLog(
                suggestion_cohorte=suggestion_cohorte,
                niveau_de_log=SuggestionLog.SuggestionLogLevel.WARNING,
                fonction_de_transformation=row["fonction_de_transformation"],
                origine_colonnes=row["origine_colonnes"],
                origine_valeurs=row["origine_valeurs"],
                destination_colonnes=row["destination_colonnes"],
                message=row["message"],
            ).save()

    for _, row in df.iterrows():
        acteur = None
        revision_acteur = None
        if identifiant_unique := row.get("identifiant_unique"):
            acteur = Acteur.objects.filter(
                identifiant_unique=identifiant_unique
            ).first()
            revision_acteur = RevisionActeur.objects.filter(
                identifiant_unique=identifiant_unique
            ).first()
        parent = (
            revision_acteur.parent
            if revision_acteur and revision_acteur.parent
            else None
        )
        suggestion_groupe = SuggestionGroupe(
            suggestion_cohorte=suggestion_cohorte,
            statut=constants.SUGGESTION_AVALIDER,
            acteur=acteur,
            revision_acteur=revision_acteur,
            parent_revision_acteur=parent,
            contexte=row["contexte"],
        )
        suggestion_groupe.save()
        suggestion: SuggestionSourceModel = SuggestionSourceModel.from_json(
            row["suggestion"]
        )
        if row.get("contexte") is not None:
            contexte: SuggestionSourceModel = SuggestionSourceModel.from_json(
                row["contexte"]
            )
        else:
            contexte: SuggestionSourceModel = SuggestionSourceModel()

        for keys in SuggestionSourceModel.get_ordered_fields():
            should_add_suggestion_unitaire = False
            for key in keys:
                if (
                    # The context value isn't defined and the suggestion is not empty
                    (getattr(contexte, key) is None and getattr(suggestion, key))
                    # The context value is defined and the suggestion value is different
                    or (
                        getattr(contexte, key) is not None
                        and getattr(suggestion, key) is not None
                        and getattr(contexte, key) != getattr(suggestion, key)
                    )
                ):
                    should_add_suggestion_unitaire = True
                    break
            if not should_add_suggestion_unitaire:
                continue
            values = []
            for key in keys:
                values.append(getattr(suggestion, key, ""))
            SuggestionUnitaire(
                suggestion_groupe=suggestion_groupe,
                statut=constants.SUGGESTION_AVALIDER,
                acteur=acteur,
                # Acteur will be updated when a source is updated
                suggestion_modele="Acteur",
                # fields should be grouped, ex : latitude and longitude
                champs=keys,
                valeurs=values,
            ).save()
            # Special case for SUPPRESSION which should be applied to its revision
            # if it exists
            if (
                suggestion_cohorte.type_action == constants.SUGGESTION_SOURCE_SUPRESSION
                and keys == ["statut"]
                and revision_acteur
            ):
                SuggestionUnitaire(
                    suggestion_groupe=suggestion_groupe,
                    statut=constants.SUGGESTION_AVALIDER,
                    acteur=acteur,
                    revision_acteur=revision_acteur,
                    parent_revision_acteur=parent,
                    suggestion_modele="RevisionActeur",
                    champs=keys,
                    valeurs=values,
                ).save()


def insert_suggestion_legacy(
    df: pd.DataFrame,
    metadata: dict,
    dag_name: str,
    run_name: str,
    type_action: str,
    df_log_error: pd.DataFrame = pd.DataFrame(),
    df_log_warning: pd.DataFrame = pd.DataFrame(),
):
    from data.models.suggestion import SuggestionLog

    if df.empty:
        return
    engine = PostgresConnectionManager().engine
    current_date = datetime.now()

    with engine.connect() as conn:
        # Insert a new suggestion
        result = conn.execute(
            """
            INSERT INTO data_suggestioncohorte
            (
                identifiant_action,
                identifiant_execution,
                type_action,
                statut,
                metadata,
                cree_le,
                modifie_le
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING ID;
        """,
            (
                dag_name,
                run_name,
                type_action,
                constants.SUGGESTION_AVALIDER,
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        suggestion_cohorte_id = result.fetchone()[0]

    # Insert suggestion_logs
    if not df_log_error.empty:
        df_log_error["suggestion_cohorte_id"] = suggestion_cohorte_id
        df_log_error["niveau_de_log"] = SuggestionLog.SuggestionLogLevel.ERROR
        df_log_error.to_sql(
            "data_suggestionlog",
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
    if not df_log_warning.empty:
        df_log_warning["suggestion_cohorte_id"] = suggestion_cohorte_id
        df_log_warning["niveau_de_log"] = SuggestionLog.SuggestionLogLevel.WARNING
        df_log_warning.to_sql(
            "data_suggestionlog",
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
    df_log_warning.to_sql(
        "data_suggestionlog",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    # Insert dag_run_change
    df["suggestion_cohorte_id"] = suggestion_cohorte_id
    df["statut"] = constants.SUGGESTION_AVALIDER
    # TODO: here the Suggestion model could be used instead of using pandas to insert
    # the data into the database
    df[["contexte", "suggestion", "suggestion_cohorte_id", "statut"]].to_sql(
        "data_suggestion",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
