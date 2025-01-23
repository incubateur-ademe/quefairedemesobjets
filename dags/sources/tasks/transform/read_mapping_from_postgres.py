import logging

import pandas as pd
from utils import logging_utils as log
from utils.db_tasks import read_data_from_postgres

logger = logging.getLogger(__name__)


def read_mapping_from_postgres(table_name: str) -> dict:
    df = read_data_from_postgres(table_name=table_name).replace({pd.NA: None})

    if df.empty:
        raise ValueError(f"DB: pas de données pour table {table_name}")

    code_id_dict = dict(zip(df["code"], df["id"]))

    log.preview(f"dict de mapping pour la table {table_name}", code_id_dict)

    return code_id_dict
