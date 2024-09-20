from unittest.mock import MagicMock

import pandas as pd
import pytest
from shapely import wkb
from shapely.geometry import Point
from utils.dag_eo_utils import (
    create_acteur_services,
    create_actors,
    create_labels,
    create_proposition_services,
    create_proposition_services_sous_categories,
    merge_duplicates,
    serialize_to_json,
)


@pytest.fixture
def df_sources_from_db():
    return pd.DataFrame({"code": ["source1", "source2"], "id": [101, 102]})


@pytest.fixture
def df_acteurtype_from_db():
    return pd.DataFrame(
        {
            "libelle": ["Type1", "Type2"],
            "code": ["ess", "commerce"],
            "id": [201, 202],
        }
    )


@pytest.fixture
def df_labels_from_db():
    return pd.DataFrame(
        {
            "code": ["ess", "ecoorganisme", "reparacteur"],
            "id": [1, 2, 3],
            "libelle": [
                "Enseigne de l'économie sociale et solidaire",
                "Labellisé Bonus Réparation EcoOrganisme",
                "Labellisé Repar'Acteur",
            ],
        }
    )


@pytest.fixture
def df_actions_from_db():
    return pd.DataFrame(
        {
            "action_name": ["reparer", "donner", "trier"],
            "id": [1, 2, 3],
            "code": ["reparer", "donner", "trier"],
        }
    )


@pytest.fixture
def df_acteur_services_from_db():
    return pd.DataFrame(
        {
            "acteur_service_name": [
                "Service de réparation",
                "Collecte par une structure spécialisée",
            ],
            "id": [10, 20],
            "code": ["Service de réparation", "Collecte par une structure spécialisée"],
        }
    )


@pytest.fixture
def df_empty_displayed_acteurs_from_db():
    return pd.DataFrame(
        columns=[
            "identifiant_unique",
            "source_id",
            "statut",
            "cree_le",
            "modifie_le",
        ]
    )


@pytest.fixture
def df_displayed_acteurs_from_db():
    return pd.DataFrame(
        {
            "identifiant_unique": ["id1", "id2"],
            "source_id": [101, 102],
            "statut": ["ACTIF", "ACTIF"],
            "cree_le": ["2024-01-01", "2024-01-01"],
            "modifie_le": ["2024-01-01", "2024-01-01"],
        }
    )


@pytest.fixture
def df_sous_categories_from_db():
    return pd.DataFrame(
        {"code": ["ecran", "smartphone, tablette et console"], "id": [101, 102]}
    )


@pytest.fixture
def db_mapping_config():
    # Can read the mapping table from json instead
    return {
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


def get_mock_ti_ps(
    db_mapping_config,
    df_actions_from_db,
    df_acteur_services_from_db,
    df_sous_categories_from_db,
    df_create_actors: pd.DataFrame = pd.DataFrame(),
    displayedpropositionservice_max_id: int = 1,
) -> MagicMock:
    mock = MagicMock()

    mock.xcom_pull.side_effect = lambda task_ids="": {
        "create_actors": {
            "df": df_create_actors,
            "config": db_mapping_config,
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
            "action": df_actions_from_db,
            "acteurservice": df_acteur_services_from_db,
            "souscategorieobjet": df_sous_categories_from_db,
        },
    }[task_ids]
    return mock


def get_mock_ti_label(
    db_mapping_config,
    df_actions_from_db,
    df_acteurtype_from_db,
    df_acteur_services_from_db,
    df_sous_categories_from_db,
    df_labels_from_db=pd.DataFrame(),
    df_create_actors: pd.DataFrame = pd.DataFrame(),
    displayedpropositionservice_max_id: int = 1,
) -> MagicMock:
    mock = MagicMock()

    mock.xcom_pull.side_effect = lambda task_ids="": {
        "create_actors": {
            "df": df_create_actors,
            "config": db_mapping_config,
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
            "action": df_actions_from_db,
            "acteurservice": df_acteur_services_from_db,
            "souscategorieobjet": df_sous_categories_from_db,
            "labelqualite": df_labels_from_db,
            "acteurtype": df_acteurtype_from_db,
        },
    }[task_ids]
    return mock


class TestCreatePropositionService:

    @pytest.mark.parametrize(
        "df_create_actors, expected_df, expected_metadata",
        [
            # No services
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 0},
            ),
            # Service Réparation
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [True],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "sous_categories": ["téléphones portables"],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Service Réemploi
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [True],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [2],
                        "acteur_id": [1],
                        "action": ["donner"],
                        "sous_categories": ["téléphones portables"],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Point Réparation
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [True],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "sous_categories": ["téléphones portables"],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # Point Collecte (tri)
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [False],
                        "point_dapport_pour_reemploi": [False],
                        "point_de_reparation": [False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [3],
                        "acteur_id": [1],
                        "action": ["trier"],
                        "sous_categories": ["téléphones portables"],
                        "id": [1],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 1},
            ),
            # All services
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["téléphones portables"],
                        "point_dapport_de_service_reparation": [True],
                        "point_dapport_pour_reemploi": [True],
                        "point_de_reparation": [True],
                        "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    }
                ),
                pd.DataFrame(
                    {
                        "action_id": [1, 2, 3],
                        "acteur_id": [1, 1, 1],
                        "action": ["reparer", "donner", "trier"],
                        "sous_categories": [
                            "téléphones portables",
                            "téléphones portables",
                            "téléphones portables",
                        ],
                        "id": [1, 2, 3],
                    },
                ),
                {"number_of_merged_actors": 0, "number_of_propositionservices": 3},
            ),
        ],
    )
    def test_create_proposition_services_services(
        self,
        df_create_actors,
        expected_df,
        expected_metadata,
        db_mapping_config,
        df_actions_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
    ):
        mock = get_mock_ti_ps(
            db_mapping_config,
            df_actions_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_create_actors=pd.DataFrame(df_create_actors),
        )

        kwargs = {"ti": mock}
        result = create_proposition_services(**kwargs)

        assert result["df"].equals(expected_df)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_multiple_actor(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
    ):
        mock = get_mock_ti_ps(
            db_mapping_config,
            df_actions_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "produitsdechets_acceptes": [
                        "téléphones portables",
                        "téléphones portables",
                    ],
                    "point_dapport_de_service_reparation": [False, False],
                    "point_dapport_pour_reemploi": [False, False],
                    "point_de_reparation": [False, False],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
                }
            ),
        )

        expected_df = pd.DataFrame(
            {
                "action_id": [3, 3],
                "acteur_id": [1, 2],
                "action": ["trier", "trier"],
                "sous_categories": ["téléphones portables", "téléphones portables"],
                "id": [1, 2],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 2,
        }

        kwargs = {"ti": mock}
        result = create_proposition_services(**kwargs)

        assert result["df"].equals(expected_df)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_multiple_product(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
    ):
        mock = get_mock_ti_ps(
            db_mapping_config,
            df_actions_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 1],
                    "produitsdechets_acceptes": [
                        "téléphones portables",
                        "écrans",
                    ],
                    "point_dapport_de_service_reparation": [True, False],
                    "point_dapport_pour_reemploi": [False, False],
                    "point_de_reparation": [False, True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
                }
            ),
        )

        df_expected = pd.DataFrame(
            {
                "action_id": [1],
                "acteur_id": [1],
                "action": ["reparer"],
                "sous_categories": ["téléphones portables | écrans"],
                "id": [1],
            }
        )
        expected_metadata = {
            "number_of_merged_actors": 0,
            "number_of_propositionservices": 1,
        }

        kwargs = {"ti": mock}
        result = create_proposition_services(**kwargs)

        assert result["df"].equals(df_expected)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_services_increment_ids(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
    ):
        mock = get_mock_ti_ps(
            db_mapping_config,
            df_actions_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1],
                    "produitsdechets_acceptes": ["téléphones portables"],
                    "point_dapport_de_service_reparation": [False],
                    "point_dapport_pour_reemploi": [False],
                    "point_de_reparation": [False],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True],
                }
            ),
            displayedpropositionservice_max_id=123,
        )

        kwargs = {"ti": mock}
        result = create_proposition_services(**kwargs)

        assert result["df"]["id"].tolist() == [123]


@pytest.fixture
def df_proposition_services():
    return pd.DataFrame(
        {
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


@pytest.fixture
def df_proposition_services_sous_categories():
    return pd.DataFrame(
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


@pytest.fixture
def mock_ti(
    df_sources_from_db,
    df_acteurtype_from_db,
    db_mapping_config,
    df_actions_from_db,
    df_acteur_services_from_db,
    df_sous_categories_from_db,
    df_labels_from_db,
    df_displayed_acteurs_from_db,
):
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
            "public_accueilli": [None, None],
        }
    )

    df_proposition_services = pd.DataFrame(
        {
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

    mock.xcom_pull.side_effect = lambda task_ids="": {
        "fetch_data_from_api": df_api,
        "create_actors": {
            "df": pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "produitsdechets_acceptes": ["téléphones portables", "ecrans"],
                    "acteur_type_id": [201, 202],
                    "point_dapport_de_service_reparation": [False, True],
                    "point_dapport_pour_reemploi": [False, False],
                    "point_de_reparation": [True, True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
                }
            ),
            "config": db_mapping_config,
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": 1,
            "action": df_actions_from_db,
            "acteurservice": df_acteur_services_from_db,
            "souscategorieobjet": df_sous_categories_from_db,
            "source": df_sources_from_db,
            "acteurtype": df_acteurtype_from_db,
            "labelqualite": df_labels_from_db,
            "displayedacteur": df_displayed_acteurs_from_db,
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
            "longitudewgs84": "longitude",
            "latitudewgs84": "latitude",
            "horaires_douverture": "horaires_description",
            "consignes_dacces": "commentaires",
        },
        "column_to_drop": ["siren"],
    }


class TestCreateActorSeriesTransformations:

    @pytest.mark.parametrize(
        "public_accueilli, expected_public_accueilli, expected_statut",
        [
            (None, None, "ACTIF"),
            ("fake", None, "ACTIF"),
            ("PARTICULIERS", "Particuliers", "ACTIF"),
            ("Particuliers", "Particuliers", "ACTIF"),
            (
                "Particuliers et professionnels",
                "Particuliers et professionnels",
                "ACTIF",
            ),
            ("PROFESSIONNELS", "Professionnels", "SUPPRIME"),
            ("Professionnels", "Professionnels", "SUPPRIME"),
        ],
    )
    def test_create_actor_public_accueilli(
        self,
        df_sources_from_db,
        df_empty_displayed_acteurs_from_db,
        public_accueilli,
        expected_public_accueilli,
        expected_statut,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "source": df_sources_from_db,
                "acteurtype": None,
                "displayedacteur": df_empty_displayed_acteurs_from_db,
            },
            "fetch_data_from_api": pd.DataFrame(
                {
                    "nom_de_lorganisme": ["Eco1"],
                    "id_point_apport_ou_reparation": ["1"],
                    "latitudewgs84": ["3.8566"],
                    "longitudewgs84": ["50.8566"],
                    "type_de_point_de_collecte": [
                        "artisan, commerce indépendant",
                    ],
                    "ecoorganisme": [
                        "source1",
                    ],
                    "produitsdechets_acceptes": ["téléphones portables"],
                    "point_dapport_de_service_reparation": [True],
                    "point_dapport_pour_reemploi": [False],
                    "point_de_reparation": [True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    "_updatedAt": ["2023-01-01 20:10:10"],
                    "cree_le": ["2021-01-01"],
                    "public_accueilli": [public_accueilli],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "public_accueilli": "public_accueilli",
                    "nom_de_lorganisme": "nom",
                    "ecoorganisme": "source_id",
                },
            },
        }
        result = create_actors(**kwargs)
        assert result["df"]["public_accueilli"][0] == expected_public_accueilli
        assert result["df"]["statut"][0] == expected_statut

    @pytest.mark.parametrize(
        "uniquement_sur_rdv,expected_uniquement_sur_rdv",
        [
            (None, False),
            (False, False),
            (True, True),
        ],
    )
    def test_create_actor_uniquement_sur_rdv(
        self,
        df_sources_from_db,
        df_empty_displayed_acteurs_from_db,
        uniquement_sur_rdv,
        expected_uniquement_sur_rdv,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "source": df_sources_from_db,
                "acteurtype": None,
                "displayedacteur": df_empty_displayed_acteurs_from_db,
            },
            "fetch_data_from_api": pd.DataFrame(
                {
                    "nom_de_lorganisme": ["Eco1"],
                    "id_point_apport_ou_reparation": ["1"],
                    "latitudewgs84": ["3.8566"],
                    "longitudewgs84": ["50.8566"],
                    "type_de_point_de_collecte": [
                        "artisan, commerce indépendant",
                    ],
                    "ecoorganisme": [
                        "source1",
                    ],
                    "produitsdechets_acceptes": ["téléphones portables"],
                    "point_dapport_de_service_reparation": [True],
                    "point_dapport_pour_reemploi": [False],
                    "point_de_reparation": [True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    "_updatedAt": ["2023-01-01 20:10:10"],
                    "cree_le": ["2021-01-01"],
                    "uniquement_sur_rdv": [uniquement_sur_rdv],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "uniquement_sur_rdv": "uniquement_sur_rdv",
                    "nom_de_lorganisme": "nom",
                    "ecoorganisme": "source_id",
                },
            },
        }
        result = create_actors(**kwargs)

        assert result["df"]["uniquement_sur_rdv"][0] == expected_uniquement_sur_rdv

    @pytest.mark.parametrize(
        "reprise,expected_reprise",
        [
            (None, None),
            ("1 pour 0", "1 pour 0"),
            ("1 pour 1", "1 pour 1"),
            ("non", "1 pour 0"),
            ("oui", "1 pour 1"),
            ("fake", None),
        ],
    )
    def test_create_actor_reprise(
        self,
        df_sources_from_db,
        df_empty_displayed_acteurs_from_db,
        reprise,
        expected_reprise,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "source": df_sources_from_db,
                "acteurtype": None,
                "displayedacteur": df_empty_displayed_acteurs_from_db,
            },
            "fetch_data_from_api": pd.DataFrame(
                {
                    "nom_de_lorganisme": ["Eco1"],
                    "id_point_apport_ou_reparation": ["1"],
                    "latitudewgs84": ["3.8566"],
                    "longitudewgs84": ["50.8566"],
                    "type_de_point_de_collecte": [
                        "artisan, commerce indépendant",
                    ],
                    "ecoorganisme": [
                        "source1",
                    ],
                    "produitsdechets_acceptes": ["téléphones portables"],
                    "point_dapport_de_service_reparation": [True],
                    "point_dapport_pour_reemploi": [False],
                    "point_de_reparation": [True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    "_updatedAt": ["2023-01-01 20:10:10"],
                    "cree_le": ["2021-01-01"],
                    "reprise": [reprise],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "reprise": "reprise",
                    "nom_de_lorganisme": "nom",
                    "ecoorganisme": "source_id",
                },
            },
        }
        result = create_actors(**kwargs)

        assert result["df"]["reprise"][0] == expected_reprise

    @pytest.mark.parametrize(
        "exclusivite_de_reprisereparation, expected_exclusivite_de_reprisereparation",
        [
            (None, False),
            ("non", False),
            ("oui", True),
            ("fake", False),
        ],
    )
    def test_create_actor_exclusivite_de_reprisereparation(
        self,
        df_sources_from_db,
        df_empty_displayed_acteurs_from_db,
        exclusivite_de_reprisereparation,
        expected_exclusivite_de_reprisereparation,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "source": df_sources_from_db,
                "acteurtype": None,
                "displayedacteur": df_empty_displayed_acteurs_from_db,
            },
            "fetch_data_from_api": pd.DataFrame(
                {
                    "nom_de_lorganisme": ["Eco1"],
                    "id_point_apport_ou_reparation": ["1"],
                    "latitudewgs84": ["3.8566"],
                    "longitudewgs84": ["50.8566"],
                    "type_de_point_de_collecte": [
                        "artisan, commerce indépendant",
                    ],
                    "ecoorganisme": [
                        "source1",
                    ],
                    "produitsdechets_acceptes": ["téléphones portables"],
                    "point_dapport_de_service_reparation": [True],
                    "point_dapport_pour_reemploi": [False],
                    "point_de_reparation": [True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True],
                    "_updatedAt": ["2023-01-01 20:10:10"],
                    "cree_le": ["2021-01-01"],
                    "exclusivite_de_reprisereparation": [
                        exclusivite_de_reprisereparation
                    ],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "exclusivite_de_reprisereparation": (
                        "exclusivite_de_reprisereparation"
                    ),
                    "nom_de_lorganisme": "nom",
                    "ecoorganisme": "source_id",
                },
            },
        }
        result = create_actors(**kwargs)

        assert (
            result["df"]["exclusivite_de_reprisereparation"][0]
            == expected_exclusivite_de_reprisereparation
        )


class TestCreateActeurServices:

    def test_create_acteur_services_empty(self, df_acteur_services_from_db):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "acteurservice": df_acteur_services_from_db,
            },
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "point_dapport_de_service_reparation": [False, False],
                        "point_dapport_pour_reemploi": [False, False],
                        "point_de_reparation": [False, False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
                    }
                ),
            },
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = create_acteur_services(**kwargs)

        assert df_result.empty
        assert df_result.columns.tolist() == [
            "acteur_id",
            "acteurservice_id",
            "acteurservice",
        ]

    def test_create_acteur_services_full(self, df_acteur_services_from_db):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "acteurservice": df_acteur_services_from_db,
            },
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "point_dapport_de_service_reparation": [True, True],
                        "point_dapport_pour_reemploi": [True, True],
                        "point_de_reparation": [True, True],
                        "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
                    }
                ),
            },
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = create_acteur_services(**kwargs)

        assert df_result.columns.tolist() == [
            "acteur_id",
            "acteurservice_id",
            "acteurservice",
        ]
        assert sorted(
            df_result.loc[df_result["acteur_id"] == 1, "acteurservice_id"].tolist()
        ) == [
            10,
            20,
        ]
        assert sorted(
            df_result.loc[df_result["acteur_id"] == 2, "acteurservice_id"].tolist()
        ) == [
            10,
            20,
        ]

    def test_create_acteur_services_only_one(self, df_acteur_services_from_db):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "acteurservice": df_acteur_services_from_db,
            },
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "point_dapport_de_service_reparation": [True, False],
                        "point_dapport_pour_reemploi": [False, True],
                        "point_de_reparation": [False, False],
                        "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
                    }
                ),
            },
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = create_acteur_services(**kwargs)

        assert df_result.columns.tolist() == [
            "acteur_id",
            "acteurservice_id",
            "acteurservice",
        ]
        assert sorted(
            df_result.loc[df_result["acteur_id"] == 1, "acteurservice_id"].tolist()
        ) == [10]
        assert sorted(
            df_result.loc[df_result["acteur_id"] == 2, "acteurservice_id"].tolist()
        ) == [20]


# serialize_to_json
class TestSerializeToJson:

    @pytest.mark.parametrize(
        "create_labels, expected_labels",
        [
            (
                pd.DataFrame(columns=["acteur_id", "labelqualite_id", "labelqualite"]),
                {0: None, 1: None},
            ),
            (
                pd.DataFrame(
                    {
                        "acteur_id": [1, 2, 2],
                        "labelqualite_id": [1, 1, 2],
                        "labelqualite": [
                            "Enseigne de l'économie sociale et solidaire",
                            "Enseigne de l'économie sociale et solidaire",
                            "Labellisé Bonus Réparation EcoOrganisme",
                        ],
                    }
                ),
                {
                    0: [
                        {
                            "acteur_id": 1,
                            "labelqualite": (
                                "Enseigne de l'économie sociale et solidaire"
                            ),
                            "labelqualite_id": 1,
                        }
                    ],
                    1: [
                        {
                            "acteur_id": 2,
                            "labelqualite": (
                                "Enseigne de l'économie sociale et solidaire"
                            ),
                            "labelqualite_id": 1,
                        },
                        {
                            "acteur_id": 2,
                            "labelqualite": "Labellisé Bonus Réparation EcoOrganisme",
                            "labelqualite_id": 2,
                        },
                    ],
                },
            ),
        ],
    )
    def test_serialize_to_json_labels(
        self,
        df_proposition_services,
        df_proposition_services_sous_categories,
        create_labels,
        expected_labels,
    ):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "df": pd.DataFrame({"identifiant_unique": [1, 2]}),
                "removed_actors": pd.DataFrame(
                    {"identifiant_unique": [3], "statut": ["SUPPRIME"]}
                ),
            },
            "create_proposition_services": {"df": df_proposition_services},
            "create_proposition_services_sous_categories": (
                df_proposition_services_sous_categories
            ),
            "create_labels": create_labels,
            "create_acteur_services": pd.DataFrame(
                columns=["acteur_id", "acteurservice_id", "acteurservice"]
            ),
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = serialize_to_json(**kwargs)
        result = df_result["all"]["df"].to_dict()
        labels = result["labels"]

        assert labels == expected_labels

    @pytest.mark.parametrize(
        "create_acteur_services, expected_acteur_services",
        [
            (
                pd.DataFrame(
                    columns=["acteur_id", "acteurservice_id", "acteurservice"]
                ),
                {0: None, 1: None},
            ),
            (
                pd.DataFrame(
                    {
                        "acteur_id": [1, 2, 2],
                        "acteurservice_id": [10, 10, 20],
                        "acteurservice": [
                            "Service de réparation",
                            "Service de réparation",
                            "Collecte par une structure spécialisée",
                        ],
                    }
                ),
                {
                    0: [
                        {
                            "acteur_id": 1,
                            "acteurservice": "Service de réparation",
                            "acteurservice_id": 10,
                        }
                    ],
                    1: [
                        {
                            "acteur_id": 2,
                            "acteurservice": "Service de réparation",
                            "acteurservice_id": 10,
                        },
                        {
                            "acteur_id": 2,
                            "acteurservice": "Collecte par une structure spécialisée",
                            "acteurservice_id": 20,
                        },
                    ],
                },
            ),
        ],
    )
    def test_serialize_to_json_acteur_services(
        self,
        df_proposition_services,
        df_proposition_services_sous_categories,
        create_acteur_services,
        expected_acteur_services,
    ):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "df": pd.DataFrame({"identifiant_unique": [1, 2]}),
                "removed_actors": pd.DataFrame(
                    {"identifiant_unique": [3], "statut": ["ACTIF"]}
                ),
            },
            "create_proposition_services": {"df": df_proposition_services},
            "create_proposition_services_sous_categories": (
                df_proposition_services_sous_categories
            ),
            "create_labels": pd.DataFrame(
                columns=["acteur_id", "labelqualite_id", "labelqualite"]
            ),
            "create_acteur_services": create_acteur_services,
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = serialize_to_json(**kwargs)
        result = df_result["all"]["df"].to_dict()
        acteur_services = result["acteur_services"]

        assert acteur_services == expected_acteur_services


class TestCreatePropositionServicesSousCategories:
    def test_create_proposition_services_sous_categories(self, mock_ti):

        kwargs = {"ti": mock_ti, "params": {}}
        df_result = create_proposition_services_sous_categories(**kwargs)

        pd.testing.assert_frame_equal(
            df_result,
            pd.DataFrame(
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
            ),
        )

    def test_create_proposition_services_sous_categories_unknown_product(
        self, db_mapping_config, df_sous_categories_from_db
    ):

        mock = MagicMock()

        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "config": db_mapping_config,
            },
            "load_data_from_postgresql": {
                "sous_categories": df_sous_categories_from_db,
            },
            "create_proposition_services": {
                "df": pd.DataFrame(
                    {
                        "action_id": [1],
                        "acteur_id": [1],
                        "action": ["reparer"],
                        "acteur_service": ["Service de réparation"],
                        "sous_categories": ["Objet inconnu dans la table de mapping"],
                        "id": [1],
                    }
                )
            },
        }[task_ids]

        kwargs = {"ti": mock, "params": {}}
        with pytest.raises(Exception):
            create_proposition_services_sous_categories(**kwargs)

    def test_create_proposition_services_sous_categories_empty_products(
        self, db_mapping_config, df_sous_categories_from_db
    ):

        mock = MagicMock()

        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "config": db_mapping_config,
            },
            "load_data_from_postgresql": {
                "sous_categories": df_sous_categories_from_db,
            },
            "create_proposition_services": {
                "df": pd.DataFrame(
                    {
                        "action_id": [1, 1],
                        "acteur_id": [1, 2],
                        "action": ["reparer", "reparer"],
                        "acteur_service": [
                            "Service de réparation",
                            "Service de réparation",
                        ],
                        "sous_categories": ["", None],
                        "id": [1, 2],
                    }
                )
            },
        }[task_ids]

        kwargs = {"ti": mock, "params": {}}
        result = create_proposition_services_sous_categories(**kwargs)
        pd.testing.assert_frame_equal(
            result,
            pd.DataFrame(
                columns=[
                    "propositionservice_id",
                    "souscategorieobjet_id",
                    "souscategorie",
                ]
            ),
        )


def test_create_actors(mock_ti, mock_config):
    kwargs = {"ti": mock_ti, "params": mock_config}
    result = create_actors(**kwargs)
    df_result = result["df"]
    metadata = result["metadata"]

    assert not df_result.empty
    assert len(df_result) == 2
    assert metadata["number_of_duplicates"] == 0
    assert metadata["added_rows"] == len(df_result)
    assert "siren" not in df_result.columns


@pytest.mark.parametrize(
    "df_displatedacteurs, df_removed_actors_expected",
    [
        # Test acteur non supprimé car existe tous dans fetch_data_from_api
        (
            pd.DataFrame(
                columns=[
                    "identifiant_unique",
                    "source_id",
                    "statut",
                    "cree_le",
                    "modifie_le",
                ]
            ),
            pd.DataFrame(
                columns=[
                    "identifiant_unique",
                    "cree_le",
                    "modifie_le",
                    "statut",
                    "event",
                ]
            ),
        ),
        # TODO: test acteur non supprimé car il n'appartient pas à la source
        (
            pd.DataFrame(
                {
                    "identifiant_unique": ["source1_1"],
                    "source_id": [101],
                    "statut": ["ACTIF"],
                    "cree_le": ["2024-01-01"],
                    "modifie_le": ["2024-01-01"],
                }
            ),
            pd.DataFrame(
                columns=[
                    "identifiant_unique",
                    "cree_le",
                    "modifie_le",
                    "statut",
                    "event",
                ]
            ),
        ),
        # TODO: test acteur suprimé car n'existe pas dans fetch_data_from_api
        (
            pd.DataFrame(
                {
                    "identifiant_unique": ["source1_0"],
                    "source_id": [101],
                    "statut": ["ACTIF"],
                    "cree_le": ["2024-01-01"],
                    "modifie_le": ["2024-01-01"],
                }
            ),
            pd.DataFrame(
                {
                    "identifiant_unique": ["source1_0"],
                    "cree_le": ["2024-01-01"],
                    "modifie_le": ["2024-01-01"],
                    "statut": ["SUPPRIME"],
                    "event": ["UPDATE_ACTOR"],
                }
            ),
        ),
    ],
)
def test_acteur_to_delete(
    df_sources_from_db, df_displatedacteurs, df_removed_actors_expected
):
    mock = MagicMock()
    mock.xcom_pull.side_effect = lambda task_ids="": {
        "load_data_from_postgresql": {
            "source": df_sources_from_db,
            "acteurtype": None,
            "displayedacteur": df_displatedacteurs,
        },
        "fetch_data_from_api": pd.DataFrame(
            {
                "id_point_apport_ou_reparation": ["1"],
                "produitsdechets_acceptes": ["12345678"],
                "nom_de_lorganisme": ["Eco1"],
                "ecoorganisme": ["source1"],
            }
        ),
    }[task_ids]

    kwargs = {
        "ti": mock,
        "params": {
            "column_mapping": {
                "id_point_apport_ou_reparation": "identifiant_externe",
                "nom_de_lorganisme": "nom",
                "ecoorganisme": "source_id",
            },
        },
    }
    result = create_actors(**kwargs)
    pd.testing.assert_frame_equal(result["removed_actors"], df_removed_actors_expected)


def test_create_reparacteurs(
    df_sources_from_db, df_acteurtype_from_db, df_empty_displayed_acteurs_from_db
):
    mock = MagicMock()
    mock.xcom_pull.side_effect = lambda task_ids="": {
        "load_data_from_postgresql": {
            "source": df_sources_from_db,
            "acteurtype": df_acteurtype_from_db,
            "displayedacteur": df_empty_displayed_acteurs_from_db,
        },
        "fetch_data_from_api": pd.DataFrame(
            {
                "reparactor_description": ["Ceci est une description du réparacteur."],
                "address_1": ["12 Rue de Rivoli"],
                "address_2": ["Bâtiment A"],
                "id_point_apport_ou_reparation": ["12345678"],
                "zip_code": ["75001"],
                "zip_code_label": ["Paris"],
                "website": ["https://www.exemple.com"],
                "email": ["contact@exemple.com"],
                "phone": ["+33-1-23-45-67-89"],
                "siret": ["123 456 789 00010"],
                "id": ["identifiant-unique-123"],
                "is_enabled": ["True"],
                "other_info": ["Informations supplémentaires sur le réparacteur."],
                "creation_date": ["2023-01-01"],
                "update_date": ["2023-06-01"],
                "reparactor_hours": ["Lun-Ven 9:00-17:00"],
                "categorie": ["categorie"],
                "categorie2": ["categorie2"],
                "categorie3": ["categorie3"],
                "latitude": ["45,3"],
                "longitude": ["48,3"],
                "url": ["abcde.fr"],
                "name": ["artisan reparacteur"],
            }
        ),
    }[task_ids]

    kwargs = {
        "ti": mock,
        "params": {
            "reparacteurs": True,
            "column_mapping": {
                "name": "nom",
                "reparactor_description": "description",
                "address_1": "adresse",
                "address_2": "adresse_complement",
                "zip_code": "code_postal",
                "zip_code_label": "ville",
                "website": "url",
                "email": "email",
                "phone": "telephone",
                "siret": "siret",
                "id": "identifiant_externe",
                "is_enabled": "statut",
                "other_info": "commentaires",
                "creation_date": "cree_le",
                "update_date": "modifie_le",
                "reparactor_hours": "horaires_description",
            },
        },
    }

    result = create_actors(**kwargs)
    df_result = result["df"]
    metadata = result["metadata"]

    assert not df_result.empty
    assert len(df_result) == 1
    assert metadata["number_of_duplicates"] == 0
    assert metadata["added_rows"] == len(df_result)
    assert "siren" not in df_result.columns
    assert "event" in df_result.columns


class TestCeateLabels:

    def test_create_reparacteur_labels(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteurtype_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
        df_labels_from_db,
    ):

        mock = get_mock_ti_label(
            db_mapping_config,
            df_actions_from_db,
            df_acteurtype_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_labels_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "label_code": ["reparacteur", ""],
                    "acteur_type_id": [202, 202],
                }
            ),
            displayedpropositionservice_max_id=123,
        )

        kwargs = {"ti": mock}

        df = create_labels(**kwargs)
        expected_dataframe_with_reparacteur_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [3],
                "labelqualite": [
                    "Labellisé Repar'Acteur",
                ],
            }
        )
        pd.testing.assert_frame_equal(df, expected_dataframe_with_reparacteur_label)

    def test_create_ess_labels(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteurtype_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
        df_labels_from_db,
    ):

        mock = get_mock_ti_label(
            db_mapping_config,
            df_actions_from_db,
            df_acteurtype_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_labels_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "acteur_type_id": [201, 202],
                }
            ),
            displayedpropositionservice_max_id=123,
        )

        kwargs = {"ti": mock}

        df = create_labels(**kwargs)
        expected_dataframe_with_ess_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [1],
                "labelqualite": [
                    "Enseigne de l'économie sociale et solidaire",
                ],
            }
        )
        pd.testing.assert_frame_equal(df, expected_dataframe_with_ess_label)

    @pytest.mark.parametrize(
        "code_ecoorganisme_bonus", ["ECOORGANISME", "ecoorganisme"]
    )
    def test_create_bonus_reparation_labels(
        self,
        db_mapping_config,
        df_actions_from_db,
        df_acteurtype_from_db,
        df_acteur_services_from_db,
        df_sous_categories_from_db,
        df_labels_from_db,
        code_ecoorganisme_bonus,
    ):

        mock = get_mock_ti_label(
            db_mapping_config,
            df_actions_from_db,
            df_acteurtype_from_db,
            df_acteur_services_from_db,
            df_sous_categories_from_db,
            df_labels_from_db,
            df_create_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "labels_etou_bonus": ["Agréé Bonus Réparation", ""],
                    "ecoorganisme": [code_ecoorganisme_bonus, "source1"],
                    "acteur_type_id": [202, 202],
                }
            ),
            displayedpropositionservice_max_id=123,
        )

        kwargs = {"ti": mock}

        df = create_labels(**kwargs)
        expected_dataframe_with_bonus_reparation_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [2],
                "labelqualite": [
                    "Labellisé Bonus Réparation EcoOrganisme",
                ],
            }
        )
        pd.testing.assert_frame_equal(
            df, expected_dataframe_with_bonus_reparation_label
        )


class TestActorsLocation:
    @pytest.mark.parametrize(
        "latitude, longitude",
        [
            (48.8566, 2.3522),
            ("48.8566", "2.3522"),
            ("48,8566", "2,3522"),
        ],
    )
    def test_create_actors_location(
        self,
        df_sources_from_db,
        df_acteurtype_from_db,
        df_empty_displayed_acteurs_from_db,
        latitude,
        longitude,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "load_data_from_postgresql": {
                "sources": df_sources_from_db,
                "acteurtype": df_acteurtype_from_db,
                "displayedacteurs": df_empty_displayed_acteurs_from_db,
            },
            "fetch_data_from_api": pd.DataFrame(
                {
                    "id_point_apport_ou_reparation": ["1"],
                    "nom_de_lorganisme": ["Actor 1"],
                    "ecoorganisme": ["source1"],
                    "source_id": ["source_id1"],
                    "latitudewgs84": [latitude],
                    "longitudewgs84": [longitude],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "nom_de_lorganisme": "nom",
                    "latitudewgs84": "latitude",
                    "longitudewgs84": "longitude",
                },
            },
        }
        result = create_actors(**kwargs)
        df_result = result["df"]

        expected_location = wkb.dumps(Point(2.3522, 48.8566)).hex()

        assert df_result["location"].iloc[0] == expected_location


class TestMergeDuplicates:

    @pytest.mark.parametrize(
        "df, expected_df",
        [
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1],
                        "produitsdechets_acceptes": [
                            " Plastic Box | Metal | Aàèë l'test",
                            " Plastic Box | Metal | Aàèë l'test",
                        ],
                        "other_column": ["A", "B"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["Aàèë l'test|Metal|Plastic Box"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 1],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                        ],
                        "other_column": [
                            "A",
                            "B",
                            "C",
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1],
                        "produitsdechets_acceptes": ["Glass|Metal|Paper|Plastic"],
                        "other_column": ["A"],
                    }
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 1, 2, 3, 3, 3],
                        "produitsdechets_acceptes": [
                            "Plastic|Metal",
                            "Metal|Glass",
                            "Paper",
                            "Glass|Plastic",
                            "Plastic|Metal",
                            "Metal",
                        ],
                        "other_column": ["A", "B", "C", "D", "E", "F"],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2, 3],
                        "produitsdechets_acceptes": [
                            "Glass|Metal|Plastic",
                            "Paper",
                            "Glass|Metal|Plastic",
                        ],
                        "other_column": ["A", "C", "D"],
                    }
                ),
            ),
        ],
    )
    def test_merge_duplicates(self, df, expected_df):

        result_df = merge_duplicates(df)

        result_df = result_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )
        expected_df = expected_df.sort_values(by="identifiant_unique").reset_index(
            drop=True
        )

        pd.testing.assert_frame_equal(result_df, expected_df)
