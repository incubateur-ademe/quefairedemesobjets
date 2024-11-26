import pandas as pd


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
