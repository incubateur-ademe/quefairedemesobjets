import logging

import pandas as pd
from crawl.config.constants import COL_URL_DB, COL_URL_ORIGINAL
from crawl.tasks.business_logic.misc.df_sort import df_sort
from django.db.models import Q
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)

from qfdmo.models import ActeurStatus, DisplayedActeur  # noqa: E402

URL_TYPES_TO_MODEL = {
    "qfdmo_displayedacteur.url": DisplayedActeur,
    # "qfdmd_lien.url": Lien,
}
URL_TYPES_TO_PK = {
    "qfdmo_displayedacteur.url": "identifiant_unique",
    # "qfdmd_lien.url": "id",
}
URL_TYPES_TO_EXTRA_FIELDS = {
    "qfdmo_displayedacteur.url": ["nom", "statut"],
    # "qfdmd_lien.url": ["titre_du_lien"],
}


def crawl_urls_candidates_read_from_db(
    url_type: str, limit: int | None = None
) -> pd.DataFrame:
    logger.info(f"{url_type=}")
    logger.info(f"{limit=}")

    if url_type not in URL_TYPES_TO_MODEL:
        raise ValueError(f"{url_type=} invalide: doit être {URL_TYPES_TO_MODEL.keys()}")

    model = URL_TYPES_TO_MODEL[url_type]
    pk = URL_TYPES_TO_PK[url_type]
    extra_fields = URL_TYPES_TO_EXTRA_FIELDS[url_type]
    entries = (
        model.objects.filter(Q(url__isnull=False) & ~Q(url__exact=""))
        .filter(statut=ActeurStatus.ACTIF)
        .order_by(COL_URL_DB)
        .values(pk, COL_URL_DB, *extra_fields)
    )
    if limit is not None:
        entries = entries[:limit]
    df = pd.DataFrame(list(entries))
    # renaming "url" to "url_original" to avoid confusion
    # as there will be a lot of URL columns (to try, success...)
    df = df.rename(columns={COL_URL_DB: COL_URL_ORIGINAL})
    return df_sort(df)
