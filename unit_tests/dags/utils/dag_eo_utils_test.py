from unittest.mock import MagicMock

import pandas as pd

import pytest

from dags.utils.dag_eo_utils import (
    create_proposition_services,
    create_proposition_services_sous_categories,
    create_actors,
)


@pytest.fixture
def mock_ti():
    mock = MagicMock()

    df_api = pd.DataFrame(
        {
            "nom_de_lorganisme": ["Eco1", "Eco2"],
            "id_point_apport_ou_reparation": ["1", "2"],
            "acteur_type_id": [
                "point d'apport volontaire privé",
                "artisan, commerce indépendant",
            ],
            "latitudewgs84": ["3.8566", "2.3522"],
            "longitudewgs84": ["50.8566", "40.8566"],
            "type_de_point_de_collecte": [
                "point d'apport volontaire privé",
                "artisan, commerce indépendant",
            ],
            "ecoorganisme": ["source1", "source2"],
            "siren": ["-", "-"],
            "adresse_format_ban": [
                "13 Rue Pierre et Marie Curie, 75005 Paris",
                "Place Jeanne d'Arc, 75013 Paris",
            ],
            "produitsdechets_acceptes": ["téléphones portables", "ecrans"],
            "point_dapport_de_service_reparation": [False, True],
            "point_dapport_pour_reemploi": [False, False],
            "point_de_reparation": [True, True],
            "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
            "adresse_complement": ["", ""],
            "enseigne_commerciale": ["enseigne1", "enseigne2"],
            "siret": [None, "33079903400085"],
            "_updatedAt": ["2023-01-01 20:10:10", "2023-01-01 20:10:10"],
            "telephone": ["+33123456789", "33123456789"],
            "cree_le": ["2021-01-01", "2021-02-01"],
            "site_web": ["", ""],
            "nom_commercial": ["Eco1", "Eco2"],
            "url": ["http://eco1.com", "http://eco2.com"],
            "email": ["contact@eco1.com", "contact@eco2.com"],
            "horaires_douverture": ["9-5 Mon-Fri", "10-6 Mon-Fri"],
            "consignes_dacces": ["", ""],
        }
    )

    df_sources = pd.DataFrame({"code": ["source1", "source2"], "id": [101, 102]})
    df_acteurtype = pd.DataFrame({"libelle": ["Type1", "Type2"], "id": [201, 202]})

    actions_df = pd.DataFrame(
        {
            "action_name": ["reparer", "donner", "trier"],
            "id": [1, 2, 3],
            "code": ["reparer", "donner", "trier"],
        }
    )
    acteur_services_df = pd.DataFrame(
        {
            "acteur_service_name": [
                "Service de réparation",
                "Collecte par une structure spécialisée",
            ],
            "id": [10, 20],
            "code": ["Service de réparation", "Collecte par une structure spécialisée"],
        }
    )
    df_proposition_services = pd.DataFrame(
        {
            "acteur_service_id": [10, 20, 10, 20],
            "action_id": [1, 3, 1, 3],
            "acteur_id": [1, 1, 2, 2],
            "action": ["reparer", "trier", "reparer", "trier"],
            "acteur_service": [
                "Service de réparation",
                "Collecte par une structure spécialisée",
                "Service de réparation",
                "Collecte par une structure spécialisée",
            ],
            "sous_categories": [
                "téléphones portables",
                "téléphones portables",
                "ecrans",
                "ecrans",
            ],
            "id": [1, 2, 3, 4],
        }
    )

    df_proposition_services_sous_categories = pd.DataFrame(
        {
            "propositionservice_id": [1, 2, 3, 4],
            "souscategorieobjet_id": [102, 102, 101, 101],
            "souscategorie": [
                "téléphones portables",
                "téléphones portables",
                "ecrans",
                "ecrans",
            ],
        }
    )

    df_sous_categories_map = pd.DataFrame(
        {"code": ["ecran", "smartphone, tablette et console"], "id": [101, 102]}
    )

    config = {
        "sous_categories": {
            "écrans": "ecran",
            "téléphones portables": "smartphone, tablette et console",
            "vêtement": "vetement",
            "linge": "linge de maison",
            "chaussure": "chaussures",
            "cartouches": "cartouches",
            "lampes": "luminaire",
            "ecrans": "ecran",
        }
    }

    mock.xcom_pull.side_effect = lambda task_ids=None: {
        "fetch_data_from_api": df_api,
        "create_actors": {
            "df": pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "produitsdechets_acceptes": ["téléphones portables", "ecrans"],
                    "point_dapport_de_service_reparation": [False, True],
                    "point_dapport_pour_reemploi": [False, False],
                    "point_de_reparation": [True, True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
                }
            ),
            "config": config,
        },
        "load_data_from_postgresql": {
            "max_pds_idx": 1,
            "actions": actions_df,
            "acteur_services": acteur_services_df,
            "sous_categories": df_sous_categories_map,
            "sources": df_sources,
            "acteurtype": df_acteurtype,
        },
        "create_proposition_services": {"df": df_proposition_services},
        "create_proposition_"
        "services_sous_categories": df_proposition_services_sous_categories,
    }[task_ids]
    return mock


@pytest.fixture
def mock_config():
    return {
        "column_mapping": {
            "id_point_apport_ou_reparation": "identifiant_externe",
            "adresse_complement": "adresse_complement",
            "type_de_point_de_collecte": "acteur_type_id",
            "telephone": "telephone",
            "siret": "siret",
            "uniquement_sur_rdv": "",
            "exclusivite_de_reprisereparation": "",
            "filiere": "",
            "public_accueilli": "",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "reprise": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
            "_updatedAt": "cree_le",
            "site_web": "url",
            "email": "email",
            "perimetre_dintervention": "",
            "longitudewgs84": "location",
            "latitudewgs84": "location",
            "horaires_douverture": "horaires_description",
            "consignes_dacces": "commentaires",
        },
        "column_to_drop": ["siren"],
    }


def test_create_proposition_services(mock_ti):

    kwargs = {"ti": mock_ti}
    result = create_proposition_services(**kwargs)
    df_result = result["df"]
    metadata = result["metadata"]
    df_result.to_csv("test.csv")
    assert not df_result.empty
    assert len(df_result) == 4
    assert df_result["acteur_service_id"].tolist() == [10, 20, 10, 20]
    assert df_result["action_id"].tolist() == [1, 3, 1, 3]
    assert metadata["number_of_merged_actors"] == 0
    assert metadata["number_of_propositionservices"] == 4


def test_create_proposition_services_sous_categories(mock_ti):
    kwargs = {"ti": mock_ti}
    df_result = create_proposition_services_sous_categories(**kwargs)

    assert not df_result.empty
    df_result.to_csv("test_pdsc.csv")
    assert df_result.columns.tolist() == [
        "propositionservice_id",
        "souscategorieobjet_id",
        "souscategorie",
    ]
    assert df_result["propositionservice_id"].tolist() == [1, 2, 3, 4]
    assert df_result["souscategorieobjet_id"].tolist() == [102, 102, 101, 101]
    assert df_result["souscategorie"].tolist() == [
        "téléphones portables",
        "téléphones portables",
        "ecrans",
        "ecrans",
    ]


def test_create_actors(mock_ti, mock_config):
    kwargs = {"ti": mock_ti, **mock_config}
    result = create_actors(**kwargs)
    df_result = result["df"]
    metadata = result["metadata"]

    assert not df_result.empty
    assert len(df_result) == 2
    assert metadata["number_of_duplicates"] == 0
    assert metadata["added_rows"] == len(df_result)
    assert "siren" not in df_result.columns
    assert "sous_categories" in result["config"]
