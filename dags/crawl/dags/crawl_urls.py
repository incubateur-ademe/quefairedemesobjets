from datetime import datetime, timedelta

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
from crawl.tasks.airflow_logic.crawl_urls_suggest_crawl_diff_https_task import (
    crawl_urls_suggest_crawl_diff_https_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_crawl_diff_other_task import (
    crawl_urls_suggest_crawl_diff_other_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_dns_fail_task import (
    crawl_urls_suggest_dns_fail_task,
)
from crawl.tasks.airflow_logic.crawl_urls_suggest_syntax_fail_task import (
    crawl_urls_suggest_syntax_fail_task,
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
        "start_date": datetime(2025, 1, 1) - timedelta(days=1),
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
    suggest_diff_https = crawl_urls_suggest_crawl_diff_https_task(dag)
    suggest_diff_other = crawl_urls_suggest_crawl_diff_other_task(dag)

    # Always reading and checking syntax
    read >> check_syntax >> suggest_syntax  # type: ignore
    # DNS depends on syntax
    check_syntax >> check_dns >> suggest_dns  # type: ignore
    # Crawl depends on DNS
    check_dns >> check_crawl >> [suggest_diff_https, suggest_diff_other]  # type: ignore

    """
    chain(
        # Although we could parallelize some of below
        # tasks, we keep linear to reduce crawl & DB load
        crawl_urls_read_urls_from_db_task(dag),
        # ✅ Checks
        crawl_urls_check_syntax_task(dag),
        crawl_urls_check_dns_task(dag),
        crawl_urls_check_crawl_task(dag),
        # 🤔 Suggestions
        # Could also be optimized by grouping
        # suggestions with their corresponding checks (e.g.
        # business receives quick DNS suggestions to review before
        # potentially long crawls)
        # Keeping them at the end for now as a failing pipeline
        # on any of the above checks could be a reason to not
        # make any suggestion
        crawl_urls_suggest_syntax_fail_task(dag),
        crawl_urls_suggest_dns_fail_task(dag),
        crawl_urls_suggest_crawl_diff_https_task(dag),
        crawl_urls_suggest_crawl_diff_other_task(dag),
    )
    """
