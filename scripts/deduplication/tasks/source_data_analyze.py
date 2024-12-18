"""Fichier placeholder pour conserver du code
utilisé pendant le test de la dédup sur PREPROD,
à savoir calculer des statistiques sur les clusters
(ex: distribution du nombre de parents par cluster)
pour pouvoir vérifier que dans l'ensemble la dédup
se passe bien



# On compte la distribution de parents par cluster
print("\nDistribution de parents par cluster")
df_parents_counts = (
    df.groupby("cluster_id")
    .agg(parents_count=("est_parent_de_revisions", "sum"))
    .reset_index()
)
print(
    df_parents_counts[
        df_parents_counts["cluster_id"].isin(
            [
                "01100_1_1",  # 0 parent
                "01110_1_1",  # 1 parent
                "01250_2_1",  # 2 parents
            ]
        )
    ]
)
df_parents_dist = df_parents_counts["parents_count"].value_counts().reset_index()
print(df_parents_dist)

   parents_count  count
0              0   2662 = parents à créer
1              1   2047 = pas de changement de parents
2              2     36 = parents à supprimer

Résultats attendus:
Net nouveaux parents = 2662 - 36
"""
