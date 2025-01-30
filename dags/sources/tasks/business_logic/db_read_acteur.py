import logging

import pandas as pd
from sources.tasks.airflow_logic.config_management import DAGConfig
from utils import logging_utils as log
from utils.django import django_setup_full

# Setup Django avant import des modèles
django_setup_full()
from qfdmo.models import Acteur  # noqa: E402

logger = logging.getLogger(__name__)


def db_read_acteur(df_normalized: pd.DataFrame, dag_config: DAGConfig):
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
    ).filter(source__code__in=unique_source_codes)

    if acteurs_count := acteurs.count():
        logger.info(f"Number of acteurs found : {acteurs_count}")
    else:
        logger.warning(
            "No acteurs found in the database, it is ok if it is the first time we"
            " ingest the source"
        )
    # transformer acteurs en dataframe
    acteurs_list = []
    expected_columns = dag_config.get_expected_columns() - {
        "location",
        "souscategorie_codes",
        "label_codes",
        "acteurservice_codes",
        "action_codes",
        "proposition_services_codes",
        "source_code",
        "acteur_type_code",
    } | {"cree_le"}
    for acteur in acteurs:
        acteur_dict = {k: getattr(acteur, k) for k in expected_columns}
        acteur_dict["source_code"] = acteur.source.code
        acteur_dict["acteur_type_code"] = acteur.acteur_type.code
        acteur_dict["label_codes"] = [label.code for label in acteur.labels.all()]
        acteur_dict["acteurservice_codes"] = [
            acteur_service.code for acteur_service in acteur.acteur_services.all()
        ]
        acteur_dict["proposition_services_codes"] = [
            {
                "action": proposition_service.action.code,
                "sous_categories": [
                    sous_categorie.code
                    for sous_categorie in proposition_service.sous_categories.all()
                ],
            }
            for proposition_service in acteur.proposition_services.all()
        ]
        acteurs_list.append(acteur_dict)

    df_acteur = pd.DataFrame(acteurs_list)

    log.preview("df_acteur retourné par la tâche", df_acteur)
    return df_acteur
