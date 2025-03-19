"""To generate names of tables used to
clone Annuaire Entreprise in our DB"""

import logging
from datetime import datetime
from typing import Optional

from clone.config.schemas import SCHEMAS_PREFIX, TABLES
from utils.raisers import raise_if

logger = logging.getLogger(__name__)


def build_timestamp_is_valid(timestamp: str) -> bool:
    """Check if a timestamp is valid"""
    try:
        datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        return True
    except ValueError:
        return False


def table_name_create(prefix: str, kind: str, build_timestamp: str) -> str:
    """Create a table name from a prefix and a name"""
    raise_if(not build_timestamp_is_valid(build_timestamp), "Timestamp invalide")
    return f"{prefix}_{kind}_{build_timestamp}"


def build_timestamp_get() -> str:
    """Return the current time as a string"""
    # return "20220101120000"  # for testing purposes
    return datetime.now().strftime("%Y%m%d%H%M%S")


def build_timestamp_from_table_name(table_name: str) -> Optional[str]:
    """Extract the build timestamp from a table name"""
    ts = table_name.split("_")[-1]
    return ts if build_timestamp_is_valid(ts) else None


def clone_ae_table_names_prepare() -> dict[str, str]:
    """Prepapre table names which we need for both
    creation AND switching the main view at the end"""
    build_ts = build_timestamp_get()
    tables = [TABLES.UNITE.kind, TABLES.ETAB.kind]
    names = {x: table_name_create(SCHEMAS_PREFIX, x, build_ts) for x in tables}
    for k, v in names.items():
        logger.info(f"Nom de la table {k}: {v}")
    return names
