import pandas as pd
from cluster.tasks.business_logic import cluster_acteurs_add_original_df_columns


def testcluster_acteurs_clusters_add_original_df_columns():
    df_clusters = pd.DataFrame(
        {
            "identifiant_unique": ["1", "3"],
            "cluster_id": ["c1", "c1"],
            "colonne_cluster": ["v1", "v3"],
        }
    )

    df_original = pd.DataFrame(
        {
            "identifiant_unique": ["1", "2", "3", "4"],
            "colonne_original": ["foo", "foo", "bar", "bar"],
        }
    )
    df = cluster_acteurs_add_original_df_columns(
        df_clusters=df_clusters, df_original=df_original
    )
    print(df)
    assert df.shape == (2, 4)
    assert df["identifiant_unique"].tolist() == ["1", "3"]
    assert df["cluster_id"].tolist() == ["c1", "c1"]
    assert df["colonne_cluster"].tolist() == ["v1", "v3"]
    assert df["colonne_original"].tolist() == ["foo", "bar"]
