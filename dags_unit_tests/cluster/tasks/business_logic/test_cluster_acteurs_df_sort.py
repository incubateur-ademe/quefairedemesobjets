import pandas as pd
import pytest
from cluster.tasks.business_logic.misc.df_sort import df_sort


class TestClusterActeursDfSort:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                "adresse": ["b", "c", "d", "a"],
                "code_postal": ["75000", "01000", "53000", "53000"],
                "ville": ["Paris", "BeB", "Laval", "Changé"],
                "source_code": ["A", "B", "C", "D"],
                "acteur_type_code": ["X", "Y", "Z", "W"],
            }
        )

    @pytest.fixture
    def df_clusters(self, df):
        # Des clusters IDs bidons, on s'en fiche pour le test
        df["cluster_id"] = [1, 2, 3, 4]
        return df

    def test_at_selection_and_normalisation_stages(self, df):
        """Démontrer que la fonction de tri fonctionne
        pour l'étape de sélection et normalisation des acteurs
        hors contexte clustering.
        """

        df_sorted = df_sort(df)
        # L'ordre des colonnes n'est pas forcément celui utiliser
        # pour ordonner les lignes, car pour les lignes on favorise
        # sémantique (ex: ville) alors que pour les colonnes on favorise
        # le debug
        assert df_sorted.columns.tolist() == [
            "acteur_type_code",  # très utile pour debug
            "code_postal",  # très utile pour sémantique
            "ville",
            "adresse",
            "source_code",
        ]
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

    def test_at_clustering_stage(self, df_clusters):
        """Utilisation de la fonction en contexte clustering"""
        df_sorted = df_sort(
            df_clusters,
            cluster_fields_exact=["ville"],
            cluster_fields_fuzzy=["adresse"],
        )
        #
        assert df_sorted.columns.tolist() == [
            "cluster_id",
            # Les codes sont remontés en haut car très
            # importants pour la phase de clustering
            "acteur_type_code",
            # On voit que les champs de clustering prennent le dessus
            # sur le champ par défaut "code_postal" (même si d'un point
            # de vue métier on ferait l'inverse, ça démontre que ça marche)
            "ville",
            "adresse",
            "source_code",
            "code_postal",
        ]
        # Toujours pas de modification de la structure de la df
        assert df_clusters.shape == df_sorted.shape
