"""Constants & models for Tables & Views"""

from typing import NamedTuple

from pydantic import BaseModel

# for tables and views
SCHEMAS_PREFIX = "clone"
VIEW_IN_USE_SUFFIX = "in_use"


class Table(BaseModel):
    kind: str
    csv_url: str
    csv_downloaded: str
    csv_unpacked: str
    # Name is not defined because it's generated dynamically
    # from prefix, kind, and timestamp


class Tables(NamedTuple):
    EA_UNITE: Table
    EA_ETAB: Table
    BAN_ADRESSES: Table
    BAN_LIEUXDITS: Table


TABLES = Tables(
    EA_UNITE=Table(
        kind="ea_unite_legale",
        csv_url="https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip",
        csv_downloaded="StockUniteLegale_utf8.zip",
        csv_unpacked="StockUniteLegale_utf8.csv",
    ),
    EA_ETAB=Table(
        kind="ea_etablissement",
        csv_url="https://files.data.gouv.fr/insee-sirene/StockEtablissement_utf8.zip",
        csv_downloaded="StockEtablissement_utf8.zip",
        csv_unpacked="StockEtablissement_utf8.csv",
    ),
    BAN_ADRESSES=Table(
        kind="ban_adresses",
        csv_url="https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz",
        csv_downloaded="adresses-france.csv.gz",
        csv_unpacked="adresses-france.csv",
    ),
    BAN_LIEUXDITS=Table(
        kind="ban_lieux_dits",
        csv_url="https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/lieux-dits-beta-france.csv.gz",
        csv_downloaded="lieux-dits-beta-france.csv.gz",
        csv_unpacked="lieux-dits-beta-france.csv",
    ),
)
