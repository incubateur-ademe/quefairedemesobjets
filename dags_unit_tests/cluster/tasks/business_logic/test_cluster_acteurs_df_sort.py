import pandas as pd

from dags.cluster.tasks.business_logic.cluster_acteurs_df_sort import (
    cluster_acteurs_df_sort,
)


class TestClusterActeursDfSort:

    def test_at_selection_phase(self):
        """Démontrer que la fonction de tri fonctionne
        pour l'étape de sélection des acteurs"""
        df = pd.DataFrame(
            {
                "adresse": ["b", "c", "d", "a"],
                "code_postal": ["75000", "01000", "53000", "53000"],
                "ville": ["Paris", "BeB", "Laval", "Changé"],
            }
        )
        df_sorted = cluster_acteurs_df_sort(df)
        # Les champs par défauts sont bien présents
        assert df_sorted.columns.tolist() == ["code_postal", "ville", "adresse"]
        # On a pas rajouté de colonnes non présentes (surtout le cluster_id)
        assert "cluster_id" not in df_sorted.columns
        # Dans l'ensemble la structure de la df n'a pas changée
        assert df.shape == df_sorted.shape
        # Et on retrouve les valeurs attendues, triées par ordre croissant
        # sachant qu'on consèrve la hiérarchie code_postal > ville > adresse
        assert df_sorted["code_postal"].tolist() == ["01000", "53000", "53000", "75000"]
        assert df_sorted["ville"].tolist() == ["BeB", "Changé", "Laval", "Paris"]
        # Donc dans notre cas le dernier champ n'est pas trié vue que
        # les cardinalités des champs précédents sont 1
        assert df_sorted["adresse"].tolist() == ["c", "a", "d", "b"]
