"""Reads URLs & acteur data from DB whilst
grouping by URL so we don't repeat URL checks
unnecessarily"""

import logging

import pandas as pd
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def crawl_urls_read_urls_from_db(limit: int | None = None) -> pd.DataFrame:
    """Get URLs to crawl from DB"""
    logger.info(f"{limit=}")
    from django.db.models import Count

    from qfdmo.models import VueActeur

    urls = (
        VueActeur.objects.get_visible_acteurs()
        .filter(
            url__isnull=False,
        )
        .exclude(url__in=["", EMPTY_ACTEUR_FIELD])
        .values("url")
        .annotate(count=Count("url"))
        .filter(count__gt=1)
        .order_by("?")
    )

    if limit is not None:
        urls = urls[:limit]
    logging.info(f"{urls=}")

    df = pd.DataFrame(urls)
    return df
