"""Reads URLs & acteur data from DB whilst
grouping by URL so we don't repeat URL checks
unnecessarily"""

import logging

import pandas as pd
from crawl.config.columns import COLS
from crawl.config.constants import SORT_COLS
from django.db.models import Q
from utils import logging_utils as log
from utils.dataframes import df_sort
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def crawl_urls_read_urls_from_db(limit: int | None = None) -> pd.DataFrame:
    """Get URLs to crawl from DB"""
    from core.models.constants import EMPTY_ACTEUR_FIELD

    logger.info(f"{limit=}")
    from qfdmo.models import ActeurStatus, DisplayedActeur

    results = (
        DisplayedActeur.objects.filter(Q(url__isnull=False) & ~Q(url__exact=""))
        .filter(~Q(url__exact=EMPTY_ACTEUR_FIELD))
        .filter(statut=ActeurStatus.ACTIF)
        # To help with lru caching DNS checks without
        # having to implement yet another level of grouping
        # (i.e. acteurs -> by URL -> by domain)
        .order_by("url")
        .values("url", "identifiant_unique", "nom")
    )
    if limit is not None:
        results = results[:limit]
    df = pd.DataFrame(results)
    df = (
        df.groupby("url")
        .apply(lambda x: x.drop(columns="url").to_dict(orient="records"))
        .reset_index()
    )
    df.columns = [COLS.URL_ORIGIN, COLS.ACTEURS]
    df = df_sort(df, sort_cols=SORT_COLS)
    logger.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("URLs à parcourir", df)
    return df
