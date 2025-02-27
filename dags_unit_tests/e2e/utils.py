"""Utilities to perform e2e tests on Airflow DAGs"""

import logging
import os
import sys
from pathlib import Path

import pendulum
from airflow.models import DagBag, DagModel, TaskInstance

logger = logging.getLogger(__name__)

# Function `days_ago` is deprecated and will be removed in Airflow 3.0.
# from airflow.utils.dates import days_ago
# TODO: remove above once we migrated to Airflow 3.0
DATE_IN_PAST = pendulum.today("UTC").add(days=-2)

PIPELINES_ROOT = Path(__file__).resolve().parent.parent.parent / "dags/"


def airflow_init() -> None:
    """Initiliazes airflow:
    - paths: need to add dags/ because DAGS make imports relative to this
    - DB: we use in-memory SQLite which is enough for now (we are not
    testing the internals of Airflow, only our DAGs)"""

    sys.path.insert(0, str(PIPELINES_ROOT))

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


def dag_get(dag_id: str) -> DagModel:
    """Looks for a DAG ID in all DAG folders and returns the DAG Model.
    Looking at: dags/{subfolder}/dags/{dag_id}.py

    🟢 pros: only parses the 1 DAG we need = time saved
    🟠 cons: requires DAG filename & ID to align

    TODO: we have in the backlog to refactor our directory
    structure into pipelines/dags which would contain all
    DAGS, in which case could simplify below to just reading
    from the only DAG folder.
    """
    logger.info(f"dag_get: 🔎 {dag_id=} searching in {PIPELINES_ROOT}")
    for path in PIPELINES_ROOT.iterdir():
        path_dag = path / "dags" / f"{dag_id}.py"
        path_rel = path_dag.relative_to(PIPELINES_ROOT)
        if path_dag.exists():
            logger.info(f"dag_get: 🟢 {dag_id=} found in {path_rel}")
            dag_bag = DagBag(dag_folder=path)
            dag_bag.collect_dags(include_examples=False, safe_mode=True)
            return dag_bag.get_dag(dag_id=dag_id)  # type: ignore
        else:
            logger.info(f"dag_get: 🟡 {dag_id=} not found in {path_rel}")
    raise ValueError(f"dag_get: 🔴 {dag_id=} not found in {PIPELINES_ROOT}")


def ti_get(tis: list[TaskInstance], task_id: str) -> TaskInstance:
    """Retrieves a Task Instance given its ID, which has the merit
    of throwing exception if we make typos in tasks, whereas if
    we only play with task indices and XCOM, XCOM can happily return
    None without complaining"""
    for ti in tis:
        if ti.task_id == task_id:
            return ti
    raise ValueError(f"task_id {task_id} not found in Task Instances")
