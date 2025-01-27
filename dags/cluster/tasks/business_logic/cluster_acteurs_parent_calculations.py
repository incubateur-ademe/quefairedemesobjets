import pandas as pd


def cluster_acteurs_parent_calculations(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des données calculées concernant les
    parents des acteurs d'une df. Cette fonction peut être
    utilisée sur n'importe quelle df dès lors que:
     - 1 ligne = 1 acteur
     - les colonnes "identifiant_unique" et "parent_id" sont présentes
    """

    assert "parent_id" in df.columns, "La colonne parent_id doit être présente"

    parent_ids_to_count = df["parent_id"].value_counts().to_dict()
    df["is_parent_current"] = df["identifiant_unique"].map(
        lambda x: x in parent_ids_to_count
    )
    df["children_count"] = df["identifiant_unique"].map(
        lambda x: parent_ids_to_count.get(x, 0)
    )

    return df
