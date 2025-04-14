"""Match acteurs from QFDMO vs. AE based on people names"""

import pandas as pd
from enrich.config import COLS
from shared.tasks.business_logic import normalize
from utils import logging_utils as log


def word_overlap_ratio(
    row: pd.Series, cols_a: list, cols_b: list
) -> tuple[list[str], float]:
    # Gather words from columns in cols_a
    words_a = set()
    for col in cols_a:
        if row[col] is not None:
            words_a.update(str(row[col]).split())

    # Gather words from columns in cols_b
    words_b = set()
    for col in cols_b:
        if row[col] is not None:
            words_b.update(str(row[col]).split())

    # Avoid division by zero
    if not words_a:
        return ([], 0.0)

    words_matched = [word for word in words_a if word in words_b]
    words_count = len(words_matched)
    ratio = words_count / len(words_a)
    if ratio > 1:
        raise ValueError(f"ratio > 1 {ratio}: {words_a} - {words_b}")
    return (words_matched, ratio)


def enrich_ae_rgpd_match(
    df: pd.DataFrame,
    match_threshold: float,
) -> pd.DataFrame:
    """Identify matches between QFDMO company names and AE's people names."""
    if df.empty:
        raise ValueError("df vide, on devrait pas être là")
    if match_threshold < 0.5 or match_threshold > 1:
        raise ValueError(f"match_threshold invalide: {match_threshold}")

    df = df.copy()

    # Matching columns
    cols_names_qfdmo = [COLS.ACTEUR_NOMS_NORMALISES]
    cols_names_ae = [COLS.AE_DIRIGEANTS_NOMS]

    # Normalization
    cols_to_norm = cols_names_qfdmo + cols_names_ae
    for col in cols_to_norm:
        df[col] = df[col].map(normalize.string_basic)

    # Matching
    df["temp"] = df.apply(
        lambda x: word_overlap_ratio(x, cols_names_qfdmo, cols_names_ae), axis=1
    )
    df[COLS.MATCH_WORDS] = df["temp"].apply(lambda x: x[0])
    df[COLS.MATCH_SCORE] = df["temp"].apply(lambda x: x[1])
    df.drop(columns=["temp"], inplace=True)

    # Selecting & previewing matches
    df_no_match = df[df[COLS.MATCH_SCORE] == 0]
    df_partial = df[(df[COLS.MATCH_SCORE] > 0) & (df[COLS.MATCH_SCORE] < 1)]
    df_perfect = df[df[COLS.MATCH_SCORE] == 1]
    df_retained = df[df[COLS.MATCH_SCORE] >= match_threshold].copy()
    log.preview_df_as_markdown("🔴 Matches non-existant (==0)", df_no_match)
    log.preview_df_as_markdown("🟡 Matches partiel (>0 & <1)", df_partial)
    log.preview_df_as_markdown("🟢 Matches parfait (==1)", df_perfect)
    log.preview_df_as_markdown(f"💾 Matches retenus (>={match_threshold})", df_retained)

    return df_retained.sort_values(COLS.MATCH_SCORE, ascending=False)
