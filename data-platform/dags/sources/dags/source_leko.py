import json

from airflow import DAG
from airflow.sdk import Param
from airflow.sdk.definitions.param import ParamsDict
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-leko",
    dag_display_name="Source - LEKO",
    default_args=DEFAULT_ARGS,
    description=(
        "Ingestion des données de l'éco-organisme LEKO à partir des données disponibles"
        " sur de Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.LEKO,
        TAGS.EMPAP,
    ],
    **default_params,
    params=ParamsDict(
        {
            "normalization_rules": json.dumps(EO_NORMALIZATION_RULES),
            "endpoint": (
                "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-leko/lines?size=10000"
            ),
            "metadata_endpoint": (
                "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-leko/schema"
            ),
            "validate_address_with_ban": False,
            "product_mapping": get_mapping_config(),
            "returnable_objects": Param(
                True,
                type="boolean",
                description_md=r"""
            Si la source de données gère des points d'apport de contenants consignés,
            alors ce paramètre doit être activé
            Les points d'apport pour ré-emploi sont alors considérés comme des points
            d'apport de contenants retournables.
            On y associera alors le geste `rapporter`.

            Si ce paramètre est inactif, alors les points d'apport pour ré-emploi sont
            considérés comme des lieux pour donner (ex : des Bennes à vêtements).
            On y associera alors le geste `donner`.
            """,
            ),
            "use_legacy_suggestions": False,
        }
    ),
) as dag:
    eo_task_chain(dag)
