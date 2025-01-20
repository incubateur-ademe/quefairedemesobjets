import pandas as pd
import pytest

from dags.cluster.tasks.business_logic.cluster_acteurs_normalize import (
    cluster_acteurs_normalize,
)


class TestClusteringActeursNormalize:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                "nom": [
                    "LE PETIT CHAT CHAT !",
                    "Château de l'île",
                    "foo & bar",
                    "",
                    None,
                ],
                "adresse": [
                    "32 RUE du CHATEAU",
                    "a",
                    "b",
                    "c",
                    "15 avenue des moulins",
                ],
                "no_words_removed": ["a b c", "aa b cc", "ccc b AAA", "", None],
                "mots_remove_2": [
                    "c b a",
                    "rue rue leon gautier",
                    "rue de de paris paris",
                    "",
                    None,
                ],
                "mots_remove_3": [
                    "rue a la montagne montagne",
                    "",
                    "boulevard",
                    "rue",
                    "",
                ],
            }
        )

    def test_default(self, df):
        df_norm = cluster_acteurs_normalize(
            df,
            # Par défaut si on ne précise pas de champs,
            # on applique la normalisation basique à tous les champs
            normalize_fields_basic=[],
            normalize_fields_no_words_size1=["nom", "adresse"],
            normalize_fields_no_words_size2_or_less=["mots_remove_2"],
            normalize_fields_no_words_size3_or_less=["mots_remove_3"],
            # Pareil, par défaut on applique à tous les champs
            normalize_fields_order_unique_words=[],
        )

        assert df_norm["nom"].tolist() == [
            "chat le petit",
            "chateau de ile",
            "bar foo",
            "",
            "",
        ]
        assert df_norm["adresse"].tolist() == [
            "32 chateau du rue",
            "",
            "",
            "",
            "15 avenue des moulins",
        ]
        assert df_norm["no_words_removed"].tolist() == [
            "a b c",
            "aa b cc",
            "aaa b ccc",
            "",
            "",
        ]
        assert df_norm["mots_remove_2"].tolist() == [
            "",
            "gautier leon rue",
            "paris rue",
            "",
            "",
        ]
        assert df_norm["mots_remove_3"].tolist() == [
            "montagne",
            "",
            "boulevard",
            "",
            "",
        ]

    def test_specific_fields_for_all_normalization(self, df):
        df_norm = cluster_acteurs_normalize(
            df,
            normalize_fields_basic=["adresse"],
            normalize_fields_no_words_size1=["adresse"],
            normalize_fields_no_words_size2_or_less=["adresse"],
            normalize_fields_no_words_size3_or_less=["adresse"],
            # Pareil, par défaut on applique à tous les champs
            normalize_fields_order_unique_words=["adresse"],
        )
        # Seul le champ adresse est normalisé car toutes les options
        # ont reçu uniquement "adresse" comme valeur
        assert df_norm["nom"].tolist() == df["nom"].tolist()
        assert df_norm["no_words_removed"].tolist() == df["no_words_removed"].tolist()
        assert df_norm["mots_remove_2"].tolist() == df["mots_remove_2"].tolist()
        assert df_norm["mots_remove_3"].tolist() == df["mots_remove_3"].tolist()

        # Les champs adresse sont normalisés
        assert df_norm["adresse"].tolist() == [
            "chateau",
            "",
            "",
            "",
            "avenue moulins",
        ]
