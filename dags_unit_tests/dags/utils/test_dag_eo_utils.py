from datetime import datetime
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
    read_acteur,
    serialize_to_json,
)


@pytest.fixture
def sources_id_by_code():
    return {
        "source1": 101,
        "source2": 102,
        "cma_reparacteur": 103,
    }


@pytest.fixture
def acteurtype_id_by_code():
    return {
        "ess": 201,
        "commerce": 202,
        "artisan": 203,
        "pav_prive": 204,
    }


@pytest.fixture
def actions_id_by_code():
    return {"reparer": 1, "donner": 2, "trier": 3}


@pytest.fixture
def labelqualite_id_by_code():
    return {"ess": 1, "label_bonus": 2, "reparacteur": 3}


@pytest.fixture
def acteurservice_id_by_code():
    return {"service_de_reparation": 10, "structure_de_collecte": 20}


# To be renamed to df_acteurs_from_db
@pytest.fixture
def df_empty_acteurs_from_db():
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
def df_acteurs_from_db():
    return pd.DataFrame(
        {
            "identifiant_unique": ["id1", "id2"],
            "source_id": [101, 102],
            "statut": ["ACTIF", "ACTIF"],
            "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
            "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
        }
    )


@pytest.fixture
def souscategorieobjet_code_by_id():
    return {"ecran": 101, "smartphone, tablette et console": 102}


def get_mock_ti_ps(
    actions_id_by_code,
    acteurservice_id_by_code,
    souscategorieobjet_code_by_id,
    df_create_actors: pd.DataFrame = pd.DataFrame(),
    displayedpropositionservice_max_id: int = 1,
) -> MagicMock:
    mock = MagicMock()

    mock.xcom_pull.side_effect = lambda task_ids="": {
        "create_actors": {
            "df": df_create_actors,
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
        },
        "read_action": actions_id_by_code,
        "read_acteurservice": acteurservice_id_by_code,
        "read_souscategorieobjet": souscategorieobjet_code_by_id,
    }[task_ids]
    return mock


def get_mock_ti_label(
    actions_id_by_code,
    acteurtype_id_by_code,
    acteurservice_id_by_code,
    souscategorieobjet_code_by_id,
    labelqualite_id_by_code=pd.DataFrame(),
    df_create_actors: pd.DataFrame = pd.DataFrame(),
    displayedpropositionservice_max_id: int = 1,
) -> MagicMock:
    mock = MagicMock()

    mock.xcom_pull.side_effect = lambda task_ids="": {
        "create_actors": {
            "df": df_create_actors,
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
        },
        "read_action": actions_id_by_code,
        "read_acteurtype": acteurtype_id_by_code,
        "read_acteurservice": acteurservice_id_by_code,
        "read_souscategorieobjet": souscategorieobjet_code_by_id,
        "read_labelqualite": labelqualite_id_by_code,
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
        actions_id_by_code,
        acteurservice_id_by_code,
        souscategorieobjet_code_by_id,
    ):
        mock = get_mock_ti_ps(
            actions_id_by_code,
            acteurservice_id_by_code,
            souscategorieobjet_code_by_id,
            df_create_actors=pd.DataFrame(df_create_actors),
        )

        kwargs = {"ti": mock}
        result = create_proposition_services(**kwargs)

        assert result["df"].equals(expected_df)
        assert result["metadata"] == expected_metadata

    def test_create_proposition_multiple_actor(
        self,
        actions_id_by_code,
        acteurservice_id_by_code,
        souscategorieobjet_code_by_id,
    ):
        mock = get_mock_ti_ps(
            actions_id_by_code,
            acteurservice_id_by_code,
            souscategorieobjet_code_by_id,
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
        actions_id_by_code,
        acteurservice_id_by_code,
        souscategorieobjet_code_by_id,
    ):
        mock = get_mock_ti_ps(
            actions_id_by_code,
            acteurservice_id_by_code,
            souscategorieobjet_code_by_id,
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
        actions_id_by_code,
        acteurservice_id_by_code,
        souscategorieobjet_code_by_id,
    ):
        mock = get_mock_ti_ps(
            actions_id_by_code,
            acteurservice_id_by_code,
            souscategorieobjet_code_by_id,
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
    sources_id_by_code,
    acteurtype_id_by_code,
    actions_id_by_code,
    acteurservice_id_by_code,
    souscategorieobjet_code_by_id,
    labelqualite_id_by_code,
    df_acteurs_from_db,
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
        },
        "load_data_from_postgresql": {
            "displayedpropositionservice_max_id": 1,
        },
        "read_acteur": df_acteurs_from_db,
        "read_action": actions_id_by_code,
        "read_acteurtype": acteurtype_id_by_code,
        "read_acteurservice": acteurservice_id_by_code,
        "read_source": sources_id_by_code,
        "read_souscategorieobjet": souscategorieobjet_code_by_id,
        "read_labelqualite": labelqualite_id_by_code,
        "create_proposition_services": {"df": df_proposition_services},
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
            "public_accueilli": "",
            "produitsdechets_acceptes": "",
            "labels_etou_bonus": "",
            "reprise": "",
            "point_de_reparation": "",
            "ecoorganisme": "source_id",
            "adresse_format_ban": "adresse",
            "nom_de_lorganisme": "nom",
            "enseigne_commerciale": "nom_commercial",
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
        sources_id_by_code,
        df_empty_acteurs_from_db,
        public_accueilli,
        expected_public_accueilli,
        expected_statut,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": None,
            "read_source": sources_id_by_code,
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
            ("oui", True),
            ("Oui", True),
            (" Oui ", True),
            ("non", False),
            ("NON", False),
            (" NON ", False),
            ("", False),
            (" ", False),
            ("fake", False),
        ],
    )
    def test_create_actor_uniquement_sur_rdv(
        self,
        sources_id_by_code,
        df_empty_acteurs_from_db,
        uniquement_sur_rdv,
        expected_uniquement_sur_rdv,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": None,
            "read_source": sources_id_by_code,
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
        sources_id_by_code,
        df_empty_acteurs_from_db,
        reprise,
        expected_reprise,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": None,
            "read_source": sources_id_by_code,
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
            (False, False),
            (True, True),
            ("oui", True),
            ("Oui", True),
            (" Oui ", True),
            ("non", False),
            ("NON", False),
            (" NON ", False),
            ("", False),
            (" ", False),
            ("fake", False),
        ],
    )
    def test_create_actor_exclusivite_de_reprisereparation(
        self,
        sources_id_by_code,
        df_empty_acteurs_from_db,
        exclusivite_de_reprisereparation,
        expected_exclusivite_de_reprisereparation,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": None,
            "read_source": sources_id_by_code,
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
    # TODO : refacto avec parametize

    def test_create_acteur_services_empty(self, acteurservice_id_by_code):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteurservice": acteurservice_id_by_code,
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
        ]

    def test_create_acteur_services_full(self, acteurservice_id_by_code):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteurservice": acteurservice_id_by_code,
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

    def test_create_acteur_services_only_one(self, acteurservice_id_by_code):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteurservice": acteurservice_id_by_code,
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
                pd.DataFrame(columns=["acteur_id", "labelqualite_id"]),
                {0: None, 1: None},
            ),
            (
                pd.DataFrame(
                    {
                        "acteur_id": [1, 2, 2],
                        "labelqualite_id": [1, 1, 2],
                    }
                ),
                {
                    0: [
                        {
                            "acteur_id": 1,
                            "labelqualite_id": 1,
                        }
                    ],
                    1: [
                        {
                            "acteur_id": 2,
                            "labelqualite_id": 1,
                        },
                        {
                            "acteur_id": 2,
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
                    {
                        "identifiant_unique": [3],
                        "statut": ["SUPPRIME"],
                        "cree_le": [datetime(2024, 1, 1)],
                    }
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
                    {
                        "identifiant_unique": [3],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                    }
                ),
            },
            "create_proposition_services": {"df": df_proposition_services},
            "create_proposition_services_sous_categories": (
                df_proposition_services_sous_categories
            ),
            "create_labels": pd.DataFrame(columns=["acteur_id", "labelqualite_id"]),
            "create_acteur_services": create_acteur_services,
        }[task_ids]

        kwargs = {"ti": mock}

        df_result = serialize_to_json(**kwargs)
        result = df_result["all"]["df"].to_dict()
        acteur_services = result["acteur_services"]

        assert acteur_services == expected_acteur_services


class TestCreatePropositionServicesSousCategories:
    def test_create_proposition_services_sous_categories(self, mock_ti):

        kwargs = {
            "ti": mock_ti,
            "params": {
                "product_mapping": {
                    "téléphones portables": "smartphone, tablette et console",
                    "ecrans": "ecran",
                }
            },
        }
        df_result = create_proposition_services_sous_categories(**kwargs)

        pd.testing.assert_frame_equal(
            df_result,
            pd.DataFrame(
                {
                    "propositionservice_id": [1, 2, 3, 4],
                    "souscategorieobjet_id": [102, 102, 101, 101],
                    "souscategorie": [
                        "smartphone, tablette et console",
                        "smartphone, tablette et console",
                        "ecran",
                        "ecran",
                    ],
                }
            ),
        )

    def test_create_proposition_services_sous_categories_unknown_product(
        self, souscategorieobjet_code_by_id
    ):

        mock = MagicMock()

        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_souscategorieobjet": souscategorieobjet_code_by_id,
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
        self, souscategorieobjet_code_by_id
    ):

        mock = MagicMock()

        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_souscategorieobjet": souscategorieobjet_code_by_id,
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
    "df_acteurs, df_removed_actors_expected",
    [
        # Test acteur non supprimé car existe tous dans fetch_data_from_api
        (
            pd.DataFrame(
                {
                    "identifiant_unique": pd.Series(dtype="str"),
                    "source_id": pd.Series(dtype="str"),
                    "statut": pd.Series(dtype="str"),
                    "cree_le": pd.Series(dtype="datetime64[ns]"),
                    "modifie_le": pd.Series(dtype="datetime64[ns]"),
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
        # TODO: test acteur non supprimé car il n'appartient pas à la source
        (
            pd.DataFrame(
                {
                    "identifiant_unique": ["source1_1"],
                    "source_id": [101],
                    "statut": ["ACTIF"],
                    "cree_le": [datetime(2024, 1, 1)],
                    "modifie_le": [datetime(2024, 1, 1)],
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
                    "cree_le": [datetime(2024, 1, 1)],
                    "modifie_le": [datetime(2024, 1, 1)],
                }
            ),
            pd.DataFrame(
                {
                    "identifiant_unique": ["source1_0"],
                    "cree_le": [datetime(2024, 1, 1)],
                    "modifie_le": [datetime(2024, 1, 1)],
                    "statut": ["SUPPRIME"],
                    "event": ["UPDATE_ACTOR"],
                }
            ),
        ),
    ],
)
def test_acteur_to_delete(sources_id_by_code, df_acteurs, df_removed_actors_expected):
    mock = MagicMock()
    mock.xcom_pull.side_effect = lambda task_ids="": {
        "read_acteur": df_acteurs,
        "read_acteurtype": None,
        "read_source": sources_id_by_code,
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
    df_removed_actors_expected["cree_le"] = pd.to_datetime(
        df_removed_actors_expected["cree_le"]
    )
    df_removed_actors_expected["modifie_le"] = pd.to_datetime(
        df_removed_actors_expected["modifie_le"]
    )
    pd.testing.assert_frame_equal(result["removed_actors"], df_removed_actors_expected)


def test_create_reparacteurs(
    sources_id_by_code, acteurtype_id_by_code, df_empty_acteurs_from_db
):
    mock = MagicMock()
    mock.xcom_pull.side_effect = lambda task_ids="": {
        "read_acteur": df_empty_acteurs_from_db,
        "read_acteurtype": acteurtype_id_by_code,
        "read_source": sources_id_by_code,
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
                "update_date": "modifie_le",
                "reparactor_hours": "horaires_description",
            },
            "source_code": "cma_reparacteur",
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


class TestCeateActorsCreeLe:
    @pytest.mark.parametrize(
        "df_acteur, df_data_from_api, expected_cree_le",
        [
            # Empty acteur
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
                    {
                        "id_point_apport_ou_reparation": ["12345678"],
                        "produitsdechets_acceptes": ["12345678"],
                        "nom_de_lorganisme": ["Eco1"],
                        "ecoorganisme": ["source1"],
                    }
                ),
                datetime.now().date(),
            ),
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["source1_id1"],
                        "source_id": [101],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 2)],
                    }
                ),
                pd.DataFrame(
                    {
                        "id_point_apport_ou_reparation": ["id1"],
                        "produitsdechets_acceptes": ["12345678"],
                        "nom_de_lorganisme": ["Eco1"],
                        "ecoorganisme": ["source1"],
                    }
                ),
                datetime(2024, 1, 1).date(),
            ),
        ],
    )
    def test_create_actors_cree_le(
        self,
        sources_id_by_code,
        acteurtype_id_by_code,
        df_acteur,
        df_data_from_api,
        expected_cree_le,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_acteur,
            "read_acteurtype": acteurtype_id_by_code,
            "read_source": sources_id_by_code,
            "fetch_data_from_api": df_data_from_api,
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
        df_result = result["df"]

        assert "cree_le" in df_result.columns
        assert df_result["cree_le"].notnull().all()
        assert df_result["cree_le"][0].date() == expected_cree_le


class TestCeateLabels:

    def test_create_reparacteur_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "labels_etou_bonus": ["reparacteur", ""],
                        "acteur_type_id": [202, 202],
                    }
                ),
            },
            "read_acteurtype": acteurtype_id_by_code,
            "read_labelqualite": labelqualite_id_by_code,
        }[task_ids]
        df = create_labels(ti=mock)

        expected_dataframe_with_reparacteur_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [3],
            }
        )

        pd.testing.assert_frame_equal(df, expected_dataframe_with_reparacteur_label)

    def test_create_ess_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "acteur_type_id": [201, 202],
                    }
                ),
            },
            "read_acteurtype": acteurtype_id_by_code,
            "read_labelqualite": labelqualite_id_by_code,
        }[task_ids]
        df = create_labels(ti=mock)

        expected_dataframe_with_ess_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [1],
            }
        )

        pd.testing.assert_frame_equal(df, expected_dataframe_with_ess_label)

    @pytest.mark.parametrize(
        "code_label_bonus", ["LABEL_BONUS", "label_bonus", "Làbèl_bônùS"]
    )
    def test_create_bonus_reparation_labels(
        self,
        acteurtype_id_by_code,
        labelqualite_id_by_code,
        code_label_bonus,
    ):

        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "create_actors": {
                "df": pd.DataFrame(
                    {
                        "identifiant_unique": [1, 2],
                        "labels_etou_bonus": [code_label_bonus, ""],
                        "acteur_type_id": [202, 202],
                    }
                ),
            },
            "read_acteurtype": acteurtype_id_by_code,
            "read_labelqualite": labelqualite_id_by_code,
        }[task_ids]
        kwargs = {"ti": mock, "params": {"label_bonus_reparation": "qualirepar"}}
        df = create_labels(**kwargs)

        expected_dataframe_with_bonus_reparation_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [2],
            }
        )

        pd.testing.assert_frame_equal(
            df, expected_dataframe_with_bonus_reparation_label
        )


class TestActorsLocation:

    # "service_a_domicile"
    def test_service_a_domicile(
        self,
        sources_id_by_code,
        acteurtype_id_by_code,
        df_empty_acteurs_from_db,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": acteurtype_id_by_code,
            "read_source": sources_id_by_code,
            "fetch_data_from_api": pd.DataFrame(
                {
                    "id_point_apport_ou_reparation": ["1", "2"],
                    "nom_de_lorganisme": ["Actor 1", "Actor 2"],
                    "ecoorganisme": ["source1", "source1"],
                    "source_id": ["source_id1", "source_id1"],
                    "service_a_domicile": ["Oui exclusivement", "Non"],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "nom_de_lorganisme": "nom",
                },
            },
        }
        result = create_actors(**kwargs)
        result_df = result["df"]

        assert len(result_df) == 1
        assert result_df["service_a_domicile"].iloc[0] == "Non"
        assert result_df["nom"].iloc[0] == "Actor 2"

    @pytest.mark.parametrize(
        "label_et_bonus, label_et_bonus_expected",
        [
            ("label_et_bonus", "label_et_bonus"),
            ("label_et_bonus1|label_et_bonus2", "label_et_bonus1|label_et_bonus2"),
            (
                "Agréé Bonus Réparation|label_et_bonus2",
                "bonus_reparation|label_et_bonus2",
            ),
        ],
    )
    def test_label_bonus(
        self,
        sources_id_by_code,
        acteurtype_id_by_code,
        df_empty_acteurs_from_db,
        label_et_bonus,
        label_et_bonus_expected,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": acteurtype_id_by_code,
            "read_source": sources_id_by_code,
            "fetch_data_from_api": pd.DataFrame(
                {
                    "id_point_apport_ou_reparation": ["1"],
                    "nom_de_lorganisme": ["Actor 1"],
                    "ecoorganisme": ["source1"],
                    "source_id": ["source_id1"],
                    "labels_etou_bonus": [label_et_bonus],
                }
            ),
        }[task_ids]

        kwargs = {
            "ti": mock,
            "params": {
                "column_mapping": {
                    "id_point_apport_ou_reparation": "identifiant_externe",
                    "nom_de_lorganisme": "nom",
                    "labels_etou_bonus": "labels_etou_bonus",
                },
                "label_bonus_reparation": "bonus_reparation",
            },
        }
        result = create_actors(**kwargs)

        assert result["df"]["labels_etou_bonus"].iloc[0] == label_et_bonus_expected

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
        sources_id_by_code,
        acteurtype_id_by_code,
        df_empty_acteurs_from_db,
        latitude,
        longitude,
    ):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_acteur": df_empty_acteurs_from_db,
            "read_acteurtype": acteurtype_id_by_code,
            "read_source": sources_id_by_code,
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


class TestReadActeur:

    @pytest.mark.parametrize(
        "df_data_from_api",
        [
            (pd.DataFrame()),
            (
                pd.DataFrame(
                    {
                        "not_ecoorganisme_column": ["value"],
                    }
                )
            ),
        ],
    )
    def test_read_acteur_raises(self, df_data_from_api, sources_id_by_code):
        mock = MagicMock()
        mock.xcom_pull.side_effect = lambda task_ids="": {
            "read_source": sources_id_by_code,
            "fetch_data_from_api": df_data_from_api,
        }[task_ids]

        with pytest.raises(ValueError):
            read_acteur(ti=mock, params={})
