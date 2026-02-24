from airflow import DAG
from airflow.models.param import Param
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-citeo",
    dag_display_name="Source - CITEO",
    default_args=DEFAULT_ARGS,
    description=(
        "Injestion des données de l'éco-organisme CITEO à partir des données disponible"
        " sur de Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.CITEO,
        TAGS.EMPAP,
    ],
    **default_params,
    params={
        "normalization_rules": EO_NORMALIZATION_RULES,
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-citeo/lines?size=10000"
        ),
        "metadata_endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-citeo/schema"
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
            d'apport de contenant retournable.
            On y associera alors le geste `rapporter`.

            Si ce paramètre est inactif, alors les points d'apport pour ré-emploi sont
            considérés comme des lieux pour donner (ex : des Bennes à vêtements).
            On y associera alors le geste `donner`.
            """,
        ),
        "use_legacy_suggestions": True,
    },
) as dag:
    eo_task_chain(dag)
