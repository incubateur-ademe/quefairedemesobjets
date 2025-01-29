"""Fichier de test bout-en-bout du DAG `cluster_acteurs_suggestions`."""

import os
from pathlib import Path

import pytest
from airflow.models import DAG, DagBag
from airflow.utils.dates import days_ago
from airflow.utils.state import State
from rich import print

from dags.cluster.config.model import ClusterConfig
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    SourceFactory,
)

# Sachant que Airflow ship par défault avec une base de données SQLite
# on devrait pouvoir l'utiliser pour les tests unitaires (il y a des
# limitations avec SQLite comme le parallelisme des DAGS, mais on s'en
# sert pas pour les tests)
os.environ["AIRFLOW__CORE__SQL_ALCHEMY_CONN"] = "sqlite:///:memory:"
# Nécessaire car sur nos tâches airflow on a la conf en ClusterConfig
# qu'on laisse Airflow géré automatiquement, ce qui implique de l'autoriser
os.environ["AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES"] = (
    "cluster.config.model.ClusterConfig"
)
from airflow.utils.db import initdb

initdb()

DAG_ID = "cluster_acteurs_suggestions"
DAG_FILE = f"{DAG_ID}.py"
# Pas besoin de charger tous les DAGs, on pointe vers le dossier
# qui contient uniquement le DAG à tester
DAG_FOLDER = str(
    Path(__file__).resolve().parent.parent.parent.parent / "dags/cluster/dags"
)
DATE_IN_PAST = days_ago(2)
TASK_IDS = [
    "cluster_acteurs_config_create",
    "cluster_acteurs_selection_from_db",
    "cluster_acteurs_normalize",
    "cluster_acteurs_suggestions_display",
    "cluster_acteurs_suggestions_validate",
    "cluster_acteurs_suggestions_to_db",
]


@pytest.mark.django_db()
class TestDagClusterActeursSuggestions:

    def test_ensure_dag_folder_is_valid(self):
        assert os.path.isdir(DAG_FOLDER)
        assert DAG_FILE in os.listdir(DAG_FOLDER)

    @pytest.fixture
    def db_testdata_write(self):
        s1 = SourceFactory(code="ecopae", id=252)
        s2 = SourceFactory(code="cyclevia", id=90)
        at1 = ActeurTypeFactory(code="decheterie", id=7)
        DisplayedActeurFactory(
            source=s1, acteur_type=at1, nom="Mon acteur s1 at1", statut="ACTIF"
        )
        DisplayedActeurFactory(
            source=s2, acteur_type=at1, nom="Mon acteur s2 at1", statut="ACTIF"
        )

    @pytest.fixture
    def conf(self, db_testdata_write):
        return {
            "dry_run": True,
            "include_source_codes": ["ecopae (id=252)", "cyclevia (id=90)"],
            "include_acteur_type_codes": ["decheterie (id=7)"],
            "include_only_if_regex_matches_nom": "dechett?erie",
            "include_if_all_fields_filled": ["code_postal"],
            "exclude_if_any_field_filled": None,
            "normalize_fields_basic": None,
            "normalize_fields_no_words_size1": ["nom"],
            "normalize_fields_no_words_size2_or_less": ["nom"],
            "normalize_fields_no_words_size3_or_less": ["nom"],
            "normalize_fields_order_unique_words": None,
            "cluster_intra_source_is_allowed": False,
            "cluster_fields_exact": ["code_postal", "ville"],
            "cluster_fields_fuzzy": ["nom", "adresse"],
            "cluster_fuzzy_threshold": 0.5,
        }

    @pytest.fixture
    def dag(self):
        # Pour la construction initiale du DagBag (une collection de DAGs)
        # voir https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/dagbag/index.html
        dag_bag = DagBag(dag_folder=DAG_FOLDER)
        dag_bag.collect_dags(include_examples=False, safe_mode=True)
        return dag_bag.get_dag(dag_id=DAG_ID)

    def test_dag_properly_parsed(self, dag):
        # Une fois qu'on a bien récupéré le DAG,
        # voir https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/dag/index.html
        assert isinstance(dag, DAG)

    def test_dag_all_tasks_properly_ordered(self, dag):
        # Si on ajoute/supprime/déplace des tâches, ce
        # test de base va nous en informer
        task_ids = [task.task_id for task in dag.tasks]
        assert task_ids == TASK_IDS

    @pytest.fixture
    def dag_test(self, dag, conf):
        # Ne pas utiliser dag.run() qui vient d'être déprécié
        # https://github.com/apache/airflow/pull/42761

        """
        Plus compliqué car il faut à la main créer une instance de DAGRun
        et gérer les états des tâches, donc pour l'instant on se contente
        de dag.test() qui marche bien pour nous
        dag.create_dagrun(
            execution_date=DATE_IN_PAST,
            start_date=DATE_IN_PAST,
            end_date=DATE_IN_PAST,
            state=DagRunState.RUNNING,
            run_type=DagRunType.MANUAL,
            conf=,
        )
        """
        dag.test(
            execution_date=DATE_IN_PAST,
            run_conf=conf,
        )
        return dag

    def test_cluster_acteur_config_create(self, dag_test):
        tis = dag_test.get_task_instances()
        ti = tis[TASK_IDS.index("cluster_acteurs_config_create")]
        assert ti.state == State.SUCCESS
        config: ClusterConfig = ti.xcom_pull(
            key="config", task_ids="cluster_acteurs_config_create"
        )
        assert config.include_source_ids == [252, 90]

    def test_cluster_acteur_selection_from_db(self, dag_test):
        tis = dag_test.get_task_instances()
        ti = tis[TASK_IDS.index("cluster_acteurs_selection_from_db")]
        assert ti.state == State.SUCCESS
        # TODO: plusieurs RUN/tests à faire:
        # 1) réussir à récupérer les acteurs de la DB
        # 2) ne pas soulever d'exception si aucun acteur n'est trouvé
        #    pour permettre au DAG de tourner en autopilote sans forcément
        #    avoir des acteurs à traiter

    def test_no_task_failed(self, dag_test):
        """Boucle sur tout les tâches pour s'assurer qu'aucune n'a échoué
        et également pour débugger plus facilement en cas d'échec."""
        tis = dag_test.get_task_instances()
        for i, task_id in enumerate(TASK_IDS):
            # https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/taskinstance/index.html
            ti = tis[i]
            print(f"Task {task_id=}: {ti.state=}")
            if ti.state == State.FAILED:
                # Récupérer les logs d'erreur est très pénible (faut passer par
                # le logger), mais bonne chance on en a pas besoin car ils sont
                # loggés sur la CLI donc savoir quelle tâche a planté suffit
                raise Exception(f"Task {task_id=} failed")
