"""
DataFrame de test utilisée par divers tests unitaires.
On essaye de constuire une dataframe qui couvre l'ensemble
des cas de figures possibles, ce qui est une tâche pénible
et source d'erreurs, d'où la volonté de centraliser cette df
"""

import pandas as pd


def df_get():
    """
    Cas de figures à couvrir:
    Cluster 1 = 0 parent existant + 2 enfants
    Cluster 2 = 1 parent existant + 2 enfants, dont 1 déjà rattaché
    Cluster 3 = 2 parents existants + 2 enfants, dont 1 déjà rattaché

    """
    return pd.DataFrame(
        {
            "cluster_id": [
                # Cluster 1
                "c1_0parent_2act",
                "c1_0parent_2act",
                # Cluster 2
                "c2_1parent_3act",
                "c2_1parent_3act",
                "c2_1parent_3act",
                # Cluster 3
                "c3_2parent_4act",
                "c3_2parent_4act",
                "c3_2parent_4act",
                "c3_2parent_4act",
            ],
            "id": [
                # Cluster 1
                "A",
                "B",
                # Cluster 2
                "C",
                "D",
                "E",
                # Cluster 3
                "F",
                "G",
                "H",
                "I",
            ],
            "parent_id": [
                # Cluster 1
                None,
                None,
                # Cluster 2
                "C",
                None,
                None,
                # Cluster 3
                "F",
                None,
                None,
                None,
            ],
            "is_parent_current": [
                # Cluster 1
                False,
                False,
                # Cluster 2
                False,
                True,
                False,
                # Cluster 3
                False,
                True,
                True,
                False,
            ],
            "is_parent_to_delete": [
                # Cluster 1
                False,
                False,
                # Cluster 2
                False,
                False,
                False,
                # Cluster 3
                False,
                True,
                False,
                False,
            ],
            "is_parent_to_keep": [
                # Cluster 1
                True,
                False,
                # Cluster 2
                False,
                True,
                False,
                # Cluster 3
                False,
                False,
                True,
                False,
            ],
        }
    )
