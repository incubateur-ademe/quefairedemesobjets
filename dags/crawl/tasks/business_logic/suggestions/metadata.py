import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def crawl_urls_suggestions_metadata(
    df_ok_same: pd.DataFrame,
    df_ok_diff: pd.DataFrame,
    df_fail: pd.DataFrame,
) -> dict:
    df_propose = pd.concat([df_ok_diff, df_fail])
    metadata = {
        "🟢 Succès ET inchangés: URLs": df_ok_same.shape[0],
        # .sum() produces a np.int64 which our DB fails to JSON serialize
        # hence the wrapping in int()
        # TODO: maybe we could create a generic serializer for all data that's
        # indented at the DB
        "🟢 Succès ET inchangés: acteurs": int(df_ok_same["acteurs"].apply(len).sum()),
        "🟡 Succès ET différents: URLs": df_ok_diff.shape[0],
        "🟡 Succès ET différents: acteurs": int(df_ok_diff["acteurs"].apply(len).sum()),
        "🔴 Échec: URLs": df_fail.shape[0],
        "🔴 Échec: acteurs": int(df_fail["acteurs"].apply(len).sum()),
        "🔢 Suggestions (🟡+🔴): URLs": df_propose.shape[0],
        "🔢 Suggestions (🟡+🔴): acteurs": int(df_propose["acteurs"].apply(len).sum()),
    }

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    df_meta = pd.DataFrame(list(metadata.items()), columns=["Cas de figure", "Nombre"])
    logger.info("Metadata de la cohorte:")
    logger.info("\n" + df_meta.to_markdown(index=False))

    return metadata
