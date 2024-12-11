import pandas as pd


def compute_parent_ps(
    df_children: pd.DataFrame,
    df_ps: pd.DataFrame,
    df_ps_sscat: pd.DataFrame,
):
    # old deduplicate_propositionservices

    # df_children_ps -> uniquement les propositions de services des enfants
    df_children_ps = df_ps.merge(
        df_children, left_on="acteur_id", right_on="identifiant_unique", how="inner"
    )
    # df_children_ps_sscat -> uniquement les liens sous catégories - propositions de
    # services des enfants
    df_children_ps_sscat = df_children_ps.merge(
        df_ps_sscat,
        left_on="id",
        right_on="propositionservice_id",
        how="inner",
    )

    df_parents_ps_sscat_detailed = (
        df_children_ps_sscat.groupby(["parent_id", "action_id"])
        .agg({"souscategorieobjet_id": lambda x: list(set(x))})
        .reset_index()
    )
    max_id = df_ps["id"].max()
    df_parents_ps_sscat_detailed["propositionservice_id"] = range(
        max_id + 1, max_id + 1 + len(df_parents_ps_sscat_detailed)
    )

    df_parents_ps_sscat = df_parents_ps_sscat_detailed.explode("souscategorieobjet_id")[
        ["propositionservice_id", "souscategorieobjet_id"]
    ]

    children_ids = df_children["identifiant_unique"].unique()

    df_children_ps_ids = df_ps[df_ps["acteur_id"].isin(children_ids)]["id"].unique()

    # suppression des ps_sscat des enfants
    df_ps_sscat = df_ps_sscat[
        ~df_ps_sscat["propositionservice_id"].isin(df_children_ps_ids)
    ]

    # ajout des ps_sscat des parents
    df_ps_sscat = pd.concat(
        [df_ps_sscat, df_parents_ps_sscat],
        ignore_index=True,
    )

    # suppression des ps des enfants
    df_ps = df_ps[~df_ps["acteur_id"].isin(children_ids)]

    # ps_sscat des parents
    df_parents_ps_sscat = df_parents_ps_sscat_detailed.rename(
        columns={"propositionservice_id": "id", "parent_id": "acteur_id"}
    )[["id", "action_id", "acteur_id"]]
    # ajout des ps des parents
    df_ps = pd.concat(
        [
            df_ps,
            df_parents_ps_sscat,
        ],
        ignore_index=True,
    )

    return {
        "df_final_ps_updated": df_ps,
        "df_final_sous_categories": df_ps_sscat,
    }
