"""Constants & models for Tables & views"""

from typing import NamedTuple

from pydantic import BaseModel
from pydantic.networks import AnyHttpUrl

# for tables and views
SCHEMAS_PREFIX = "clone_ae"

URL_UNITE = "https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip"
URL_ETAB = "https://files.data.gouv.fr/insee-sirene/StockEtablissement_utf8.zip"


class Table(BaseModel):
    kind: str
    csv_url: AnyHttpUrl
    csv_filestem: str
    # Name is not defined because it's generated dynamically
    # from prefix, kind, and timestamp


class Tables(NamedTuple):
    UNITE: Table
    ETAB: Table


TABLES = Tables(
    UNITE=Table(
        kind="unite_legale",
        csv_url=URL_UNITE,  # type: ignore
        csv_filestem="StockUniteLegale_utf8",
    ),
    ETAB=Table(
        kind="etablissement",
        csv_url=URL_ETAB,  # type: ignore
        csv_filestem="StockEtablissement_utf8",
    ),
)


VIEW_NAME_UNITE = f"{SCHEMAS_PREFIX}_unite_legale_in_use"
VIEW_NAME_ETAB = f"{SCHEMAS_PREFIX}_etablissement_in_use"
