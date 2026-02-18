"""Utilities to perform e2e tests on Airflow DAGs"""

import logging
import os
import sys
from pathlib import Path

from airflow.models import TaskInstance

logger = logging.getLogger(__name__)

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


def ti_get(tis: list[TaskInstance], task_id: str) -> TaskInstance:
    """Retrieves a Task Instance given its ID, which has the merit
    of throwing exception if we make typos in tasks, whereas if
    we only play with task indices and XCOM, XCOM can happily return
    None without complaining"""
    for ti in tis:
        if ti.task_id == task_id:
            return ti
    raise ValueError(f"task_id {task_id} not found in Task Instances")
