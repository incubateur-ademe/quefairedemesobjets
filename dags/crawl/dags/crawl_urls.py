from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from crawl.tasks.airflow_logic.candidates.groupby_url_task import (
    crawl_urls_candidates_groupby_url_task,
)
from crawl.tasks.airflow_logic.candidates.read_from_db_task import (
    crawl_urls_candidates_read_from_db_task,
)
from crawl.tasks.airflow_logic.solve.reach_task import crawl_urls_solve_reach_task
from crawl.tasks.airflow_logic.solve.syntax_task import crawl_urls_solve_syntax_task
from crawl.tasks.airflow_logic.suggestions.metadata_task import (
    crawl_urls_suggestions_metadata_task,
)
from crawl.tasks.airflow_logic.suggestions.prepare_task import (
    crawl_urls_suggestions_prepare_task,
)
from crawl.tasks.airflow_logic.suggestions.write_to_db import (
    crawl_urls_suggestions_write_to_db_task,
)

URL_TYPES = [
    "qfdmo_displayedacteur.url",
]
URL_CRAWL_MIN = 1
URL_CRAWL_MAX = 1000
URL_CRAWL_DEFAULT = 50
UI_PARAMS_SEPARATOR_SELECTION = r"""

# Sélection des d'URLs
"""

with DAG(
    dag_id="crawl_urls_suggestions",
    dag_display_name="🔗 Crawl - URLs - Suggestions",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        # Une date bidon dans le passée pour
        # par que Airflow "attende" que la date
        # soit atteinte
        "start_date": datetime(2025, 1, 1),
        # Notre donnée n'étant pas versionnée dans le temps,
        # faire du catchup n'a pas de sense
        "catchup": False,
        "email_on_failure": False,
        "email_on_retry": False,
        # Les tâches de ce DAG ne devrait pas avoir de problème
        # de perf donc 0 retries par défaut
        "retries": 0,
    },
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
            URL_CRAWL_DEFAULT,
            type="integer",
            minimum=1,
            maximum=URL_CRAWL_MAX,
            description_md=f"""**🔢 Nombre d'URLs** à parcourir
            minimum={URL_CRAWL_MIN}
            maximum={URL_CRAWL_MAX}""",
        ),
    },
) as dag:
    chain(
        crawl_urls_candidates_read_from_db_task(dag),
        crawl_urls_candidates_groupby_url_task(dag),
        crawl_urls_solve_syntax_task(dag),
        crawl_urls_solve_reach_task(dag),
        crawl_urls_suggestions_metadata_task(dag),
        crawl_urls_suggestions_prepare_task(dag),
        crawl_urls_suggestions_write_to_db_task(dag),
    )
