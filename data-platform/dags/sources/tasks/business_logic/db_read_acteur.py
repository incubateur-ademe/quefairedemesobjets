import logging

import pandas as pd
from sources.tasks.airflow_logic.config_management import DAGConfig
from utils import logging_utils as log
from utils.django import django_setup_full, get_model_fields

django_setup_full()


logger = logging.getLogger(__name__)


# TODO: To be factorized with PYDANTIC classes
def db_read_acteur(df_normalized: pd.DataFrame, dag_config: DAGConfig):
    from qfdmo.models import Acteur

    if "source_code" not in df_normalized.columns:
        raise ValueError(
            "La colonne source_codes est requise dans la dataframe normalisée"
        )
    unique_source_codes = df_normalized["source_code"].unique()

    acteurs = Acteur.objects.prefetch_related(
        "proposition_services",
        "proposition_services__action",
        "proposition_services__sous_categories",
        "source",
        "acteur_type",
        "acteur_services",
        "perimetre_adomiciles",
    ).filter(source__code__in=unique_source_codes)

    if acteurs_count := acteurs.count():
        logger.info(f"Number of acteurs found : {acteurs_count}")
    else:
        logger.warning(
            "No acteurs found in the database, it is ok if it is the first time we"
            " ingest the source"
        )
    acteurs_list = []

    # we need expected_columns which exists in the model
    # The relationships are resolved in the loop
    expected_columns = (dag_config.get_expected_columns()) & set(
        get_model_fields(Acteur, with_relationships=False, latlong=True)
    )
    for acteur in acteurs:
        acteur_dict = {k: getattr(acteur, k) for k in expected_columns}
        acteur_dict["source_code"] = acteur.source.code
        acteur_dict["acteur_type_code"] = acteur.acteur_type.code
        acteur_dict["label_codes"] = [label.code for label in acteur.labels.all()]
        acteur_dict["acteur_service_codes"] = [
            acteur_service.code for acteur_service in acteur.acteur_services.all()
        ]
        acteur_dict["proposition_service_codes"] = [
            {
                "action": ps.action.code,
                "sous_categories": [
                    sscat.code for sscat in ps.sous_categories.all().order_by("code")
                ],
            }
            for ps in acteur.proposition_services.all().order_by("action__code")
        ]
        acteur_dict["perimetre_adomicile_codes"] = [
            {"type": perimetre.type, "valeur": perimetre.valeur}
            for perimetre in acteur.perimetre_adomiciles.all().order_by(
                "type", "valeur"
            )
        ]
        acteurs_list.append(acteur_dict)
    if acteurs_list:
        df_acteur = pd.DataFrame(acteurs_list)
    else:
        # Set an empty dataframe with the expected columns to avoid errors on next tasks
        df_acteur = pd.DataFrame(columns=list(dag_config.get_expected_columns()))

    log.preview("df_acteur retourné par la tâche", df_acteur)
    return df_acteur
