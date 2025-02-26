"""Generates metadata for the suggestions
based on previous check tasks. If no suggestions,
then metadata is None so airflow task can skip rest of pipeline"""

import logging

import pandas as pd
from crawl.config.constants import (
    COL_ACTEURS,
    SCENARIO_DNS_FAIL,
    SCENARIO_SYNTAX_FAIL,
    SCENARIO_TOTAL,
    SCENARIO_URL_FAIL,
    SCENARIO_URL_OK_DIFF,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def df_not_empty(df: pd.DataFrame) -> bool:
    """Helper to handle df.empty + None case
    in case of optional task not executing and
    thus xcom being None"""
    return df is not None and not df.empty


def df_acteurs_count(df: pd.DataFrame) -> int:
    """Helper to count acteurs in DF, converting
    to int to be JSON compatible"""
    return int(df[COL_ACTEURS].apply(len).sum())


def crawl_urls_suggestions_metadata(
    df_syntax_fail: pd.DataFrame,
    df_dns_fail: pd.DataFrame,
    df_urls_ok_diff: pd.DataFrame,
    df_urls_fail: pd.DataFrame,
) -> dict[str, int] | None:
    """Calculates metadata for the suggestions cohort"""
    meta = {}
    URLS = ": # URLs"
    ACTEURS = ": # Acteurs"

    if df_not_empty(df_syntax_fail):
        meta[SCENARIO_SYNTAX_FAIL + URLS] = len(df_syntax_fail)
        meta[SCENARIO_SYNTAX_FAIL + ACTEURS] = df_acteurs_count(df_syntax_fail)

    if df_not_empty(df_dns_fail):
        meta[SCENARIO_DNS_FAIL + URLS] = len(df_dns_fail)
        meta[SCENARIO_DNS_FAIL + ACTEURS] = df_acteurs_count(df_dns_fail)

    if df_not_empty(df_urls_ok_diff):
        meta[SCENARIO_URL_OK_DIFF + URLS] = len(df_urls_ok_diff)
        meta[SCENARIO_URL_OK_DIFF + ACTEURS] = df_acteurs_count(df_urls_ok_diff)

    if df_not_empty(df_urls_fail):
        meta[SCENARIO_URL_FAIL + URLS] = len(df_urls_fail)
        meta[SCENARIO_URL_FAIL + ACTEURS] = df_acteurs_count(df_urls_fail)

    if not meta:
        return None

    meta[SCENARIO_TOTAL + URLS] = sum(meta[k] for k in meta.keys() if k.endswith(URLS))
    meta[SCENARIO_TOTAL + ACTEURS] = sum(
        meta[k] for k in meta.keys() if k.endswith(ACTEURS)
    )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df_meta = pd.DataFrame(list(meta.items()), columns=["Cas de figure", "Nombre"])
    logger.info("Metadata de la cohorte:")
    logger.info("\n" + df_meta.to_markdown(index=False))

    return meta
