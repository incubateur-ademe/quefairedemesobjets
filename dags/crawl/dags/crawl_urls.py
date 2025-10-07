from airflow import DAG
from airflow.models.param import Param
from crawl.tasks.airflow_logic.crawl_urls_check_crawl_task import (
    crawl_urls_check_crawl_task,
)
from crawl.tasks.airflow_logic.crawl_urls_check_dns_task import (
    crawl_urls_check_dns_task,
)
from crawl.tasks.airflow_logic.crawl_urls_check_syntax_task import (
    crawl_urls_check_syntax_task,
)
from crawl.tasks.airflow_logic.crawl_urls_read_urls_from_db_task import (
    crawl_urls_read_urls_from_db_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_crawl_diff_other_task import (
    crawl_urls_suggest_crawl_diff_other_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_crawl_diff_standard_task import (
    crawl_urls_suggest_crawl_diff_standard_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_dns_fail_task import (
    crawl_urls_suggest_dns_fail_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_syntax_fail_task import (
    crawl_urls_suggest_syntax_fail_task,
)
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

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
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    },
    start_date=START_DATES.YESTERDAY,
    catchup=False,
    schedule=None,
    description=("Un DAG pour parcourir des URLs et suggérer des corrections"),
    tags=[TAGS.ENRICH, TAGS.CRAWL, TAGS.ACTEURS, TAGS.URL, TAGS.SUGGESTIONS],
    params={
        "dry_run": Param(
            True,
            type="boolean",
            description_md=f"""🚱 Si coché, les URLs seront parcourues
            mais les suggestions pas écrites en base.
            {UI_PARAMS_SEPARATOR_SELECTION}""",
        ),
        "urls_limit": Param(
            None,
            type=["null", "integer"],
            minimum=1,
            description_md=f"""**🔢 Nombre d'URLs** à parcourir.
            Si pas spécifié = toutes les URLs

            {UI_PARAMS_SEPARATOR_VERIFICATION}""",
        ),
        "urls_check_crawl": Param(
            False,
            type="boolean",
            description_md="""**🤖 Vérification CRAWL**: on cherche à parcourir
            les URLs pour voir si leurs pages sont accessibles
            et/ou si elles redirigent""",
        ),
    },
) as dag:
    read = crawl_urls_read_urls_from_db_task(dag)
    check_syntax = crawl_urls_check_syntax_task(dag)
    check_dns = crawl_urls_check_dns_task(dag)
    check_crawl = crawl_urls_check_crawl_task(dag)
    suggest_syntax = crawl_urls_suggest_syntax_fail_task(dag)
    suggest_dns = crawl_urls_suggest_dns_fail_task(dag)
    suggest_diff_standard = crawl_urls_suggest_crawl_diff_standard_task(dag)
    suggest_diff_other = crawl_urls_suggest_crawl_diff_other_task(dag)

    # Always reading and checking syntax
    read >> check_syntax >> suggest_syntax  # type: ignore
    # DNS depends on syntax
    check_syntax >> check_dns >> suggest_dns  # type: ignore
    # Crawl depends on DNS
    check_dns >> check_crawl >> [suggest_diff_standard, suggest_diff_other]  # type: ignore
