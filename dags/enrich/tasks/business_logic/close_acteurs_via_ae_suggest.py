"""Generate suggestions from matches"""

import logging

import pandas as pd
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def close_acteurs_via_ae_suggest(
    df: pd.DataFrame,
    identifiant_action: str,
    identifiant_execution: str,
    dry_run: bool = True,
) -> list[dict]:
    """Generate suggestions from matches"""
    pass
