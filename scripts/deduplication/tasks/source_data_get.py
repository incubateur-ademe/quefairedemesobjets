from pathlib import Path

import numpy as np
import pandas as pd
from rich import print


def source_data_get(filepath_csv: Path) -> pd.DataFrame:
    """Récupération des données sources. On the garde
    que le strict nécessaire en terme de données retournées
    (à savoir cluster_id <-> identifiant_unique), tous le reste
    des données doit provenir de la DB

    Args:
        filepath_csv: chemin vers le fichier CSV

    Returns:
        df: propositions de clusters, 1 ligne = cluster_id <-> identifiant_unique
    """
    print("\nDF SOURCE: lecture")
    df = pd.read_csv(filepath_csv).replace({np.nan: None})
    print(f"Tous les clusters: {df.shape}")
    # On ne garde que les clusters avec au moins 2 acteurs
    df = df.groupby("cluster_id").filter(lambda x: len(x) >= 2).reset_index(drop=True)
    print(f"On garde que clusters de taille 2+: {df.shape}")
    identifiants = set(df["identifiant_unique"].unique())
    cluster_ids = set(df["cluster_id"].unique())
    print(f"{len(identifiants)=}")
    print(f"{len(cluster_ids)=}")
    assert len(cluster_ids) > 0, "Aucun cluster trouvé"
    return df[["cluster_id", "identifiant_unique"]]
