import pandas as pd
import pytest
from sources.tasks.business_logic.compute_link_tables import compute_link_tables


@pytest.fixture
def df_acteur():
    return pd.DataFrame(
        {
            "identifiant_unique": [1, 2, 3],
            "acteurservice_codes": [[], [], []],
            "label_codes": [[], [], []],
            "proposition_services_codes": [[], [], []],
            "source_code": ["source1", "source2", "source1"],
            "acteur_type_code": ["commerce", "ess", "pav_prive"],
        }
    )


def test_compute_link_tables_success(
    df_acteur,
    acteurservice_id_by_code,
    labelqualite_id_by_code,
    actions_id_by_code,
    souscategorieobjet_code_by_id,
    source_id_by_code,
    acteurtype_id_by_code,
):

    result = compute_link_tables(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
        labelqualite_id_by_code=labelqualite_id_by_code,
        actions_id_by_code=actions_id_by_code,
        souscats_id_by_code=souscategorieobjet_code_by_id,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )
    expected_result = pd.DataFrame(
        {
            "identifiant_unique": [1, 2, 3],
            "acteurservice_codes": [[], [], []],
            "label_codes": [[], [], []],
            "proposition_services_codes": [[], [], []],
            "source_code": ["source1", "source2", "source1"],
            "acteur_type_code": ["commerce", "ess", "pav_prive"],
            "acteur_services": [[], [], []],
            "labels": [[], [], []],
            "proposition_services": [[], [], []],
            "source_id": [1, 2, 1],
            "acteur_type_id": [202, 201, 204],
        }
    )
    pd.testing.assert_frame_equal(
        result.reset_index(drop=True), expected_result.reset_index(drop=True)
    )


def test_compute_link_tables_acteur_services(
    df_acteur,
    acteurservice_id_by_code,
    labelqualite_id_by_code,
    actions_id_by_code,
    souscategorieobjet_code_by_id,
    source_id_by_code,
    acteurtype_id_by_code,
):
    df_acteur["acteurservice_codes"] = [
        ["service_de_reparation"],
        ["structure_de_collecte"],
        ["service_de_reparation", "structure_de_collecte"],
    ]
    result = compute_link_tables(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
        labelqualite_id_by_code=labelqualite_id_by_code,
        actions_id_by_code=actions_id_by_code,
        souscats_id_by_code=souscategorieobjet_code_by_id,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )
    expected_acteur_services = pd.Series(
        [
            [{"acteurservice_id": 10, "acteur_id": 1}],
            [{"acteurservice_id": 20, "acteur_id": 2}],
            [
                {"acteurservice_id": 10, "acteur_id": 3},
                {"acteurservice_id": 20, "acteur_id": 3},
            ],
        ]
    )
    assert result["acteur_services"].equals(expected_acteur_services)


def test_compute_link_tables_labels(
    df_acteur,
    acteurservice_id_by_code,
    labelqualite_id_by_code,
    actions_id_by_code,
    souscategorieobjet_code_by_id,
    source_id_by_code,
    acteurtype_id_by_code,
):
    df_acteur["label_codes"] = [["ess"], ["label_bonus"], ["reparacteur", "ess"]]
    result = compute_link_tables(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
        labelqualite_id_by_code=labelqualite_id_by_code,
        actions_id_by_code=actions_id_by_code,
        souscats_id_by_code=souscategorieobjet_code_by_id,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )
    expected_labels = pd.Series(
        [
            [{"acteur_id": 1, "labelqualite_id": 1}],
            [{"acteur_id": 2, "labelqualite_id": 2}],
            [
                {"acteur_id": 3, "labelqualite_id": 3},
                {"acteur_id": 3, "labelqualite_id": 1},
            ],
        ]
    )
    assert result["labels"].equals(expected_labels)


def test_compute_link_tables_propositionservices(
    df_acteur,
    acteurservice_id_by_code,
    labelqualite_id_by_code,
    actions_id_by_code,
    souscategorieobjet_code_by_id,
    source_id_by_code,
    acteurtype_id_by_code,
):
    df_acteur["proposition_services_codes"] = [
        [{"action": "reparer", "sous_categories": ["smartphone, tablette et console"]}],
        [{"action": "donner", "sous_categories": ["ecran"]}],
        [
            {
                "action": "reparer",
                "sous_categories": ["smartphone, tablette et console"],
            },
            {
                "action": "donner",
                "sous_categories": ["ecran", "smartphone, tablette et console"],
            },
        ],
    ]
    result = compute_link_tables(
        df_acteur=df_acteur,
        acteurservice_id_by_code=acteurservice_id_by_code,
        labelqualite_id_by_code=labelqualite_id_by_code,
        actions_id_by_code=actions_id_by_code,
        souscats_id_by_code=souscategorieobjet_code_by_id,
        source_id_by_code=source_id_by_code,
        acteurtype_id_by_code=acteurtype_id_by_code,
    )
    expected_proposition_services = pd.Series(
        [
            [
                {
                    "acteur_id": 1,
                    "action_id": 1,
                    "action": "reparer",
                    "sous_categories": ["smartphone, tablette et console"],
                    "pds_sous_categories": [
                        {
                            "souscategorie": "smartphone, tablette et console",
                            "souscategorieobjet_id": 102,
                        }
                    ],
                }
            ],
            [
                {
                    "acteur_id": 2,
                    "action_id": 2,
                    "action": "donner",
                    "sous_categories": ["ecran"],
                    "pds_sous_categories": [
                        {
                            "souscategorie": "ecran",
                            "souscategorieobjet_id": 101,
                        }
                    ],
                }
            ],
            [
                {
                    "acteur_id": 3,
                    "action_id": 1,
                    "action": "reparer",
                    "sous_categories": ["smartphone, tablette et console"],
                    "pds_sous_categories": [
                        {
                            "souscategorie": "smartphone, tablette et console",
                            "souscategorieobjet_id": 102,
                        }
                    ],
                },
                {
                    "acteur_id": 3,
                    "action_id": 2,
                    "action": "donner",
                    "sous_categories": ["ecran", "smartphone, tablette et console"],
                    "pds_sous_categories": [
                        {
                            "souscategorie": "ecran",
                            "souscategorieobjet_id": 101,
                        },
                        {
                            "souscategorie": "smartphone, tablette et console",
                            "souscategorieobjet_id": 102,
                        },
                    ],
                },
            ],
        ]
    )
    assert result["proposition_services"].equals(expected_proposition_services)
