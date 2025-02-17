"""Definition of our DAG's tasks in their run order:
 - to refer to tasks via constants
 - to fetch task instances via indices such as:
     tis = dag.get_task_instances()
     ti = tis[TASKS_ORDERED.index(TASK_CONFIG_CREATE)]
"""

from dags.cluster.tasks.airflow_logic.task_ids import (
    TASK_CLUSTERS_DISPLAY,
    TASK_CLUSTERS_VALIDATE,
    TASK_CONFIG_CREATE,
    TASK_NORMALIZE,
    TASK_PARENTS_CHOOSE_DATA,
    TASK_PARENTS_CHOOSE_NEW,
    TASK_SELECTION,
    TASK_SUGGESTIONS_DISPLAY,
    TASK_SUGGESTIONS_TO_DB,
)

TASKS_ORDERED = [
    TASK_CONFIG_CREATE,
    TASK_SELECTION,
    TASK_NORMALIZE,
    TASK_PARENTS_CHOOSE_NEW,
    TASK_PARENTS_CHOOSE_DATA,
    TASK_CLUSTERS_DISPLAY,
    TASK_CLUSTERS_VALIDATE,
    TASK_SUGGESTIONS_DISPLAY,
    TASK_SUGGESTIONS_TO_DB,
]
