import pandas as pd
from rich import print
from sources.tasks.source_data_normalize import df_normalize_sinoe


def test_df_normalize_sinoe():

    df = pd.DataFrame(
        (
            # pas gardée car produitsdechets_acceptes manquant
            {
                "identifiant_externe": "DECHET_1",
                "ANNEE": 2024,
                "_geopoint": "48.81618976894698,2.3558767483676513",
                "produitsdechets_acceptes": None,
                "public_accueilli": "DMA",
            },
            {
                "identifiant_externe": "DECHET_2",
                "ANNEE": 2024,
                "_geopoint": "48.4812237361283,3.120109493179493",
                "produitsdechets_acceptes": "01.1|07.25|07.6",
                "public_accueilli": "DMA/PRO",
            },
            {
                "identifiant_externe": "DECHET_3",
                "ANNEE": 2024,
                "_geopoint": "48.4812237361283,3.120109493179493",
                "produitsdechets_acceptes": "07.6",
                "public_accueilli": "DMA/PRO",
            },
            # pas gardée car 01.22=Déchets alcalins manquant dans product_mapping
            {
                "identifiant_externe": "DECHET_4",
                "ANNEE": 2024,
                "_geopoint": "48.4812237361283,3.120109493179493",
                "produitsdechets_acceptes": "NP|01.22",
                "public_accueilli": "DMA/PRO",
            },
        )
    )
    source_code = "ADEME_SINOE_Decheteries"
    params = {
        "source_code": source_code,
        "dechet_mapping": {
            # Entrées dans notre product_mapping
            "01.1": "Solvants usés",
            "07.25": "Papiers cartons mêlés triés",
            "07.6": "Déchets textiles",
            # Entrées manquantes dans notre product_mapping
            "01.22": "Déchets alcalins",
            # Cas spécial: on ignore
            "NP": "Non précisé",
        },
        "product_mapping": {
            "Solvants usés": "Produits chimiques - Solvants",
            "Papiers cartons mêlés triés": [
                "papiers_graphiques",
                "emballage_carton",
            ],
            "Déchets textiles": ["vêtement", "linge de maison"],
        },
    }
    df = df_normalize_sinoe(df, params)
    print(df.to_dict(orient="records"))
    assert df["identifiant_externe"].tolist() == ["DECHET_2", "DECHET_3"]


if __name__ == "__main__":
    test_df_normalize_sinoe()
