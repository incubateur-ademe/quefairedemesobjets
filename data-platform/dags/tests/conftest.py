import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from django.core.management import call_command
from faker import Faker


def pytest_configure(config):
    project_root = Path(__file__).resolve().parents[3]

    dags_path = project_root / "data-platform" / "dags"
    webapp_path = project_root / "webapp"

    for path in (dags_path, webapp_path):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "acteur_types",
            "actions",
        )


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
def df_acteur_from_db():
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


@pytest.fixture
def source_id_by_code():
    return {
        "source1": 1,
        "source2": 2,
        "source3": 3,
    }


@pytest.fixture
def dag_config():
    from dags.sources.tasks.airflow_logic.config_management import DAGConfig

    return DAGConfig.model_validate(
        {
            "normalization_rules": [
                {
                    "column": col,
                    "value": Faker().word(),
                }
                for col in [
                    "identifiant_unique",
                    "identifiant_externe",
                    "nom",
                    "acteur_service_codes",
                    "label_codes",
                    "proposition_service_codes",
                    "source_code",
                    "acteur_type_code",
                    "statut",
                ]
            ],
            "endpoint": "https://example.com/api",
            "product_mapping": {"product1": "code1"},
        }
    )
