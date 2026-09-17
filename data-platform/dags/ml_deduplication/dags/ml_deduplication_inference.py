"""DAG that provisions an on-demand Scaleway instance to run ML-deduplication
inference, then terminates it once done.

Lifecycle (create -> wait -> run -> destroy):
  - create : `scw instance server create` with a cloud-init user-data that
             installs Docker and pre-pulls the inference image. Also creates the
             locked-down security group and a flexible IP.
  - wait   : poll until the instance is running and the image is present (SSH).
  - run    : SSH in and `docker run` the inference image, reading acteurs from
             the warehouse DB and writing clusters/predictions back to a table.
  - destroy: terminate the instance, release the IP and delete the security
             group (always runs, even on failure).

All provisioning is done through the scw CLI from the scheduler container; the
instance is ephemeral (one per run) so no declarative Terraform is needed.
"""

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Param, dag
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

DAG_ID = "ml_deduplication_inference"
SCRIPTS = "/opt/airflow/scripts/infrastructure"

# SSH keys are injected as container env (like SCW_*, DB_WAREHOUSE):
# ML_DEDUPLICATION_SSH_PUB_KEY (public, injected via cloud-init at creation) and
# ML_DEDUPLICATION_SSH_KEY (path to the private key used to SSH into the instance).

DEFAULT_IMAGE = "rg.fr-par.scw.cloud/ns-ml-deduplication-inference/ml-deduplication-inference:latest"

PARAMS = {
    "acteurs_table": Param(
        "",
        type="string",
        description_md="""Table/view name to read acteurs from in the warehouse DB
            (e.g. `qfdmo_vueacteur`). Required.""",
    ),
    "output_table": Param(
        "",
        type="string",
        description_md="""Base name of the DB table(s) to upload results to.
            Clusters go to `<output_table>_clusters`, candidate pairs to
            `<output_table>_predictions`. When empty, results are only written
            to parquet inside the instance and are lost at termination.""",
    ),
    "image_ref": Param(
        DEFAULT_IMAGE,
        type="string",
        description_md="Inference image reference to pull and run.",
    ),
    "model_threshold": Param(
        None,
        type=["null", "number"],
        description_md="Threshold to use for inference (default: model's best).",
    ),
    "linkage_column": Param(
        None,
        type=["null", "string"],
        description_md="Column holding the dataset id for cross-dataset linkage.",
    ),
    "split_by_departement": Param(
        False,
        type="boolean",
        description_md="Run inference split per departement.",
    ),
}


@dag(
    dag_id=DAG_ID,
    dag_display_name="ML - Deduplication - Inference sur instance on-demand",
    schedule=None,
    start_date=START_DATES.DEFAULT,
    is_paused_upon_creation=False,
    max_active_runs=1,
    catchup=False,
    tags=[TAGS.ML, TAGS.DEDUPLICATION, TAGS.SCALEWAY],
    params=PARAMS,
)
def ml_deduplication_inference():
    env = {
        "ML_DEDUPLICATION_ACTEURS_TABLE": "{{ params.acteurs_table }}",
        "ML_DEDUPLICATION_OUTPUT_TABLE": "{{ params.output_table }}",
        "ML_DEDUPLICATION_IMAGE": "{{ params.image_ref }}",
        "ML_DEDUPLICATION_MODEL_THRESHOLD": "{{ params.model_threshold or '' }}",
        "ML_DEDUPLICATION_LINKAGE_COLUMN": "{{ params.linkage_column or '' }}",
        "ML_DEDUPLICATION_SPLIT_BY_DEPARTEMENT": (
            "{{ '1' if params.split_by_departement else '0' }}"
        ),
    }

    create_instance = BashOperator(
        task_id="create_instance",
        bash_command=f"{SCRIPTS}/ml_deduplication_instance_create.sh ",
        env=env,
    )

    wait_for_ready = BashOperator(
        task_id="wait_for_ready",
        bash_command=f"{SCRIPTS}/ml_deduplication_instance_wait.sh ",
        env=env,
    )

    run_inference = BashOperator(
        task_id="run_inference",
        bash_command=f"{SCRIPTS}/ml_deduplication_inference_run.sh ",
        env=env,
    )

    # Always clean up, whether or not upstream tasks succeeded.
    destroy_instance = BashOperator(
        task_id="destroy_instance",
        bash_command=f"{SCRIPTS}/ml_deduplication_instance_destroy.sh ",
        env=env,
        trigger_rule="all_done",
    )

    create_instance >> wait_for_ready >> run_inference >> destroy_instance


ml_deduplication_inference()
