"""Read acteur with non conform code postal"""

import logging

import pandas as pd
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def _get_df_acteurs_with_invalid_cp(model) -> pd.DataFrame:
    acteurs = (
        model.objects.exclude(code_postal__regex=r"^[0-9]{5}$")
        .exclude(code_postal__isnull=True)
        .exclude(code_postal="")
        .values("identifiant_unique", "code_postal")
    )
    return pd.DataFrame(acteurs)


def db_read_acteur_cp() -> pd.DataFrame:
    from qfdmo.models.acteur import Acteur

    return _get_df_acteurs_with_invalid_cp(Acteur)


def db_read_revision_acteur_cp() -> pd.DataFrame:
    from qfdmo.models.acteur import RevisionActeur

    return _get_df_acteurs_with_invalid_cp(RevisionActeur)
