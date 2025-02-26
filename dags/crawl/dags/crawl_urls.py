from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from crawl.tasks.airflow_logic.crawl_urls_check_dns_task import (
    crawl_urls_check_dns_task,
)
from crawl.tasks.airflow_logic.crawl_urls_check_syntax_task import (
    crawl_urls_check_syntax_task,
)
from crawl.tasks.airflow_logic.crawl_urls_read_from_db_task import (
    crawl_urls_candidates_read_from_db_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggestions_metadata_task import (
    crawl_urls_suggestions_metadata_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggestions_prepare_task import (
    crawl_urls_suggestions_prepare_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggestions_to_db_task import (
    crawl_urls_suggestions_to_db_task,
)

URL_TYPES = [
    "qfdmo_displayedacteur.url",
]
UI_PARAMS_SEPARATOR_SELECTION = r"""

# 🔎 Sélection des d'URLs ⬇️
"""

UI_PARAMS_SEPARATOR_VERIFICATION = r"""

# ✅ Vérification des URLs ⬇️
"""

with DAG(
    dag_id="crawl_urls_suggestions",
    dag_display_name="🔗 Crawl - URLs - Suggestions",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2025, 1, 1),
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    catchup=False,
    schedule_interval=None,
    description=("Un DAG pour parcourir des URLs et suggérer des corrections"),
    tags=["crawl", "acteurs", "url", "suggestions"],
    params={
        "dry_run": Param(
            True,
            type="boolean",
            description_md=f"""🚱 Si coché, les URLs seront parcourues
            mais les suggestions pas écrites en base.
            {UI_PARAMS_SEPARATOR_SELECTION}""",
        ),
        "urls_type": Param(
            URL_TYPES[0],
            enum=URL_TYPES,
            description_md="""**🔗 Type d'URL** à parcourir.
            On pourra faire fonctionner le DAG en mode automatique qui
            alterne les différents types""",
        ),
        "urls_limit": Param(
            None,
            type=["null", "integer"],
            minimum=1,
            description_md=f"""**🔢 Nombre d'URLs** à parcourir.
            Si pas spécifié = toutes les URLs

            {UI_PARAMS_SEPARATOR_VERIFICATION}""",
        ),
        "urls_check_syntax": Param(
            True,
            # Airflow v2 doesn't support read-only params, to achieve
            # the equivalent, we use enum with only [True], which
            # does render a checkbox which can be changed BUT will prevent
            # launching DAG if set to False
            enum=[True],
            description_md="""**✍️ Vérification syntaxe**: on vérifie **toujours**
            que la syntaxe des URLs est bonne, sinon on ne cherche même pas à
            les parcourir""",
        ),
        "urls_check_dns": Param(
            True,
            # Airflow v2 doesn't support read-only params, to achieve
            # the equivalent, we use enum with only [True], which
            # does render a checkbox which can be changed BUT will prevent
            # launching DAG if set to False
            enum=[True],
            description_md="""**🔤 Vérification DNS**: on vérifie **toujours**
            que les domaines sont joignables, sinon on ne cherche même pas à
            parcourir leur URLs""",
        ),
    },
) as dag:
    chain(
        crawl_urls_candidates_read_from_db_task(dag),
        crawl_urls_check_syntax_task(dag),
        crawl_urls_check_dns_task(dag),
        crawl_urls_suggestions_metadata_task(dag),
        crawl_urls_suggestions_prepare_task(dag),
        crawl_urls_suggestions_to_db_task(dag),
    )
