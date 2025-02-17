"""Utilities to help us loads Airflow and DAGs

TODO: once we start performing e2e for multiple DAGS
this should be moved to a shared folder
"""

import os
from pathlib import Path

from airflow.models import DagBag, DagModel, TaskInstance

DAG_ID = "cluster_acteur_suggestions"
DAG_FOLDER = Path(__file__).resolve().parent.parent.parent.parent / "dags/cluster/dags"
DAG_FILE = DAG_FOLDER / f"{DAG_ID}.py"
assert DAG_FILE.exists(), f"Can't find {DAG_FILE=}"


def airflow_init() -> None:
    """Initiliazes airflow in-memory for now"""

    # TODO: change to its own PostgreSQL deployment to be ISO with
    # our prod Airflow. For now we tolerate this since our airflow
    # setup is sqlite-compatible
    os.environ["AIRFLOW__CORE__SQL_ALCHEMY_CONN"] = "sqlite:///:memory:"
    # Needed because we pass ClusterConfig via XCOM
    os.environ["AIRFLOW__CORE__ALLOWED_DESERIALIZATION_CLASSES"] = (
        "cluster.config.model.ClusterConfig"
    )
    from airflow.utils.db import initdb

    initdb()


def dag_get() -> DagModel:
    """Returns our parsed DAG from the DagBag"""
    dag_bag = DagBag(dag_folder=DAG_FOLDER)
    dag_bag.collect_dags(include_examples=False, safe_mode=True)
    return dag_bag.get_dag(dag_id=DAG_ID)  # type: ignore


def ti_get(tis: list[TaskInstance], task_id: str) -> TaskInstance:
    for ti in tis:
        if ti.task_id == task_id:
            return ti
    raise ValueError(f"task_id {task_id} not found in Task Instances")
