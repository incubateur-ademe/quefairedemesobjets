from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest
from shapely import wkb
from shapely.geometry import Point
from sources.tasks.business_logic.propose_acteur_changes import propose_acteur_changes
from sources.tasks.business_logic.propose_acteur_services import propose_acteur_services
from sources.tasks.business_logic.propose_acteur_to_delete import (
    propose_acteur_to_delete,
)
from sources.tasks.business_logic.propose_labels import propose_labels
from sources.tasks.business_logic.propose_services_sous_categories import (
    propose_services_sous_categories,
)
from sources.tasks.business_logic.serialize_to_json import db_data_prepare
from sources.tasks.transform.transform_df import merge_duplicates


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
        "propose_acteur_changes": {
            "df": df_create_actors,
        },
        "db_read_propositions_max_id": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
        },
        "db_read_action": actions_id_by_code,
        "db_read_acteurservice": acteurservice_id_by_code,
        "db_read_souscategorieobjet": souscategorieobjet_code_by_id,
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
        "propose_acteur_changes": {
            "df": df_create_actors,
        },
        "db_read_propositions_max_id": {
            "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
        },
        "db_read_action": actions_id_by_code,
        "db_read_acteurtype": acteurtype_id_by_code,
        "db_read_acteurservice": acteurservice_id_by_code,
        "db_read_souscategorieobjet": souscategorieobjet_code_by_id,
        "db_read_labelqualite": labelqualite_id_by_code,
    }[task_ids]
    return mock


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
            "identifiant_unique": ["1", "2"],
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
        "source_data_normalize": df_api,
        "propose_acteur_changes": {
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
        "db_read_propositions_max_id": {
            "displayedpropositionservice_max_id": 1,
        },
        "db_read_acteur": df_acteurs_from_db,
        "db_read_action": actions_id_by_code,
        "db_read_acteurtype": acteurtype_id_by_code,
        "db_read_acteurservice": acteurservice_id_by_code,
        "db_read_source": sources_id_by_code,
        "db_read_souscategorieobjet": souscategorieobjet_code_by_id,
        "db_read_labelqualite": labelqualite_id_by_code,
        "propose_services": {"df": df_proposition_services},
        "services_sous_categories": df_proposition_services_sous_categories,
    }[task_ids]
    return mock


@pytest.fixture
def mock_config():
    return {
        "column_to_drop": ["siren"],
    }


class TestCreateActeurServices:
    # TODO : refacto avec parametize
    def test_create_acteur_services_empty(self, acteurservice_id_by_code):

        df_result = propose_acteur_services(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "point_dapport_de_service_reparation": [False, False],
                    "point_dapport_pour_reemploi": [False, False],
                    "point_de_reparation": [False, False],
                    "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
                }
            ),
            acteurservice_id_by_code=acteurservice_id_by_code,
        )

        assert df_result.empty
        assert df_result.columns.tolist() == [
            "acteur_id",
            "acteurservice_id",
        ]

    def test_create_acteur_services_full(self, acteurservice_id_by_code):

        df_result = propose_acteur_services(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "point_dapport_de_service_reparation": [True, True],
                    "point_dapport_pour_reemploi": [True, True],
                    "point_de_reparation": [True, True],
                    "point_de_collecte_ou_de_reprise_des_dechets": [True, True],
                }
            ),
            acteurservice_id_by_code=acteurservice_id_by_code,
        )

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

        df_result = propose_acteur_services(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "point_dapport_de_service_reparation": [True, False],
                    "point_dapport_pour_reemploi": [False, True],
                    "point_de_reparation": [False, False],
                    "point_de_collecte_ou_de_reprise_des_dechets": [False, False],
                }
            ),
            acteurservice_id_by_code=acteurservice_id_by_code,
        )

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


# db_data_prepare
class TestSerializeToJson:

    @pytest.mark.parametrize(
        "propose_labels, expected_labels",
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
        propose_labels,
        expected_labels,
    ):

        df_result = db_data_prepare(
            df_acteur_to_delete=pd.DataFrame(
                {
                    "identifiant_unique": [3],
                    "statut": ["ACTIF"],
                    "cree_le": [datetime(2024, 1, 1)],
                }
            ),
            df_actors=pd.DataFrame({"identifiant_unique": [1, 2]}),
            df_ps=df_proposition_services,
            df_pssc=df_proposition_services_sous_categories,
            df_labels=propose_labels,
            df_acteur_services=pd.DataFrame(
                columns=["acteur_id", "acteurservice_id", "acteurservice"]
            ),
        )
        result = df_result["all"]["df"].to_dict()
        labels = result["labels"]

        assert labels == expected_labels

    @pytest.mark.parametrize(
        "propose_acteur_services, expected_acteur_services",
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
        propose_acteur_services,
        expected_acteur_services,
    ):
        df_result = db_data_prepare(
            df_acteur_to_delete=pd.DataFrame(
                {
                    "identifiant_unique": [3],
                    "statut": ["ACTIF"],
                    "cree_le": [datetime(2024, 1, 1)],
                }
            ),
            df_actors=pd.DataFrame({"identifiant_unique": [1, 2]}),
            df_ps=df_proposition_services,
            df_pssc=df_proposition_services_sous_categories,
            df_labels=pd.DataFrame(columns=["acteur_id", "labelqualite_id"]),
            df_acteur_services=propose_acteur_services,
        )
        result = df_result["all"]["df"].to_dict()
        acteur_services = result["acteur_services"]

        assert acteur_services == expected_acteur_services


class TestCreatePropositionServicesSousCategories:
    def test_create_proposition_services_sous_categories(
        self, souscategorieobjet_code_by_id
    ):
        df_result = propose_services_sous_categories(
            df_ps=pd.DataFrame(
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
            ),
            souscats_id_by_code=souscategorieobjet_code_by_id,
            product_mapping={
                "téléphones portables": "smartphone, tablette et console",
                "ecrans": "ecran",
            },
        )

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
            "db_read_souscategorieobjet": souscategorieobjet_code_by_id,
            "propose_services": {
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
            propose_services_sous_categories(**kwargs)

    def test_create_proposition_services_sous_categories_empty_products(
        self, souscategorieobjet_code_by_id
    ):
        with pytest.raises(ValueError):
            propose_services_sous_categories(
                df_ps=pd.DataFrame(
                    {
                        "action_id": [1, 1],
                        "acteur_id": [1, 2],
                        "action": ["reparer", "reparer"],
                        "acteur_service": [
                            "Service de réparation",
                            "Service de réparation",
                        ],
                        "sous_categories": ["", []],
                        "id": [1, 2],
                    }
                ),
                souscats_id_by_code=souscategorieobjet_code_by_id,
                product_mapping={},
            )


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
                        "identifiant_unique": ["source1_id1"],
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
                        "identifiant_unique": ["source1_id1"],
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
        df_acteur,
        df_data_from_api,
        expected_cree_le,
    ):
        result = propose_acteur_changes(
            df=df_data_from_api,
            df_acteurs=df_acteur,
        )
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
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "labels_etou_bonus": ["reparacteur", ""],
                    "acteur_type_id": [202, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

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
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "acteur_type_id": [201, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

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
        df = propose_labels(
            df_actors=pd.DataFrame(
                {
                    "identifiant_unique": [1, 2],
                    "labels_etou_bonus": [code_label_bonus, ""],
                    "acteur_type_id": [202, 202],
                }
            ),
            labelqualite_id_by_code=labelqualite_id_by_code,
            acteurtype_id_by_code=acteurtype_id_by_code,
        )

        expected_dataframe_with_bonus_reparation_label = pd.DataFrame(
            {
                "acteur_id": [1],
                "labelqualite_id": [2],
            }
        )

        pd.testing.assert_frame_equal(
            df, expected_dataframe_with_bonus_reparation_label
        )


class TestActorServiceADomicile:

    # "service_a_domicile"
    def test_service_a_domicile(
        self,
        df_empty_acteurs_from_db,
    ):

        result = propose_acteur_changes(
            df=pd.DataFrame(
                {
                    "identifiant_unique": ["1", "2"],
                    "service_a_domicile": ["Oui exclusivement", "Non"],
                }
            ),
            df_acteurs=df_empty_acteurs_from_db,
        )
        result_df = result["df"]

        assert len(result_df) == 1
        assert result_df["service_a_domicile"].iloc[0] == "Non"
        assert result_df["identifiant_unique"].iloc[0] == "2"


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
        df_empty_acteurs_from_db,
        latitude,
        longitude,
    ):
        result = propose_acteur_changes(
            df=pd.DataFrame(
                {
                    "identifiant_unique": ["1"],
                    "latitude": [latitude],
                    "longitude": [longitude],
                }
            ),
            df_acteurs=df_empty_acteurs_from_db,
        )
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


@pytest.fixture
def metadata():
    return


class TestActeurToDelete:
    @pytest.mark.parametrize(
        (
            "df_acteurs_from_db1, df_acteurs_for_source, df_expected_acteur_to_delete,"
            " expected_metadata"
        ),
        [
            # No deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
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
                {"number_of_removed_actors": 0},
            ),
            # No Deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2", "id3", "id4"],
                        "statut": ["ACTIF", "ACTIF", "INACTIF", "SUPPRIME"],
                        "cree_le": [
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                        ],
                        "modifie_le": [
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                            datetime(2024, 1, 1),
                        ],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
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
                {"number_of_removed_actors": 0},
            ),
            # Deletion
            (
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1", "id2"],
                        "statut": ["ACTIF", "ACTIF"],
                        "cree_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1), datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id1"],
                        "statut": ["ACTIF"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1)],
                    }
                ),
                pd.DataFrame(
                    {
                        "identifiant_unique": ["id2"],
                        "cree_le": [datetime(2024, 1, 1)],
                        "modifie_le": [datetime(2024, 1, 1)],
                        "statut": ["SUPPRIME"],
                        "event": ["UPDATE_ACTOR"],
                    }
                ),
                {"number_of_removed_actors": 1},
            ),
        ],
    )
    def test_get_acteur_to_delete(
        self,
        df_acteurs_from_db1,
        df_acteurs_for_source,
        df_expected_acteur_to_delete,
        expected_metadata,
    ):
        result = propose_acteur_to_delete(
            df_acteurs_for_source=df_acteurs_for_source,
            df_acteurs_from_db=df_acteurs_from_db1,
        )
        df_returned_acteur_to_delete = result["df_acteur_to_delete"]

        pd.testing.assert_frame_equal(
            df_returned_acteur_to_delete.reset_index(drop=True),
            df_expected_acteur_to_delete.reset_index(drop=True),
            check_dtype=False,
        )
        assert result["metadata"] == expected_metadata
