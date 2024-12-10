import pandas as pd
from sources.tasks.transform.transform_column import (
    clean_number,
    clean_siren,
    clean_siret,
)


def clean_siret_and_siren(row):
    if "siret" in row:
        row["siret"] = clean_siret(row["siret"])
    else:
        row["siret"] = None
    if "siren" in row:
        row["siren"] = clean_siren(row["siren"])
    else:
        row["siren"] = (
            row["siret"][:9] if "siret" in row and row["siret"] is not None else None
        )
    return row[["siret", "siren"]]


def merge_duplicates(
    df, group_column="identifiant_unique", merge_column="produitsdechets_acceptes"
):

    df_duplicates = df[df.duplicated(group_column, keep=False)]
    df_non_duplicates = df[~df.duplicated(group_column, keep=False)]

    df_merged_duplicates = (
        df_duplicates.groupby(group_column)
        .agg(
            {
                **{
                    col: "first"
                    for col in df.columns
                    if col != merge_column and col != group_column
                },
                merge_column: merge_produits_accepter,
            }
        )
        .reset_index()
    )

    # Concatenate the non-duplicates and merged duplicates
    df_final = pd.concat([df_non_duplicates, df_merged_duplicates], ignore_index=True)

    return df_final


def merge_produits_accepter(group):
    produits_sets = set()
    for produits in group:
        produits_sets.update([produit.strip() for produit in produits.split("|")])
    return "|".join(sorted(produits_sets))


def clean_phone_number(number, code_postal):

    number = clean_number(number)

    if number is None:
        return None

    if len(number) == 9 and code_postal and int(code_postal) < 96000:
        number = "0" + number

    if number.startswith("33"):
        number = "0" + number[2:]

    if len(number) < 6:
        return None

    return number
