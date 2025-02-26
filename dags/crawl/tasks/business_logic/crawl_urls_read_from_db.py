"""Reads URLs & acteur data from DB whilst
grouping by URL so we don't repeat URL checks
unnecessarily"""

import logging

import pandas as pd
from crawl.config.constants import COL_ACTEURS, COL_URL_ORIGINAL, SORT_COLS
from django.db.models import Q
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils import logging_utils as log
from utils.dataframes import df_sort
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def crawl_urls_candidates_read_from_db(
    url_type: str, limit: int | None = None
) -> pd.DataFrame:
    logger.info(f"{url_type=}")
    logger.info(f"{limit=}")
    from qfdmo.models import ActeurStatus, DisplayedActeur

    results = (
        DisplayedActeur.objects.filter(Q(url__isnull=False) & ~Q(url__exact=""))
        .filter(~Q(url__exact=EMPTY_ACTEUR_FIELD))
        .filter(statut=ActeurStatus.ACTIF)
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
    df.columns = [COL_URL_ORIGINAL, COL_ACTEURS]
    df = df_sort(df, sort_cols=SORT_COLS)
    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    log.preview_df_as_markdown("URLs à parcourir", df)
    return df
