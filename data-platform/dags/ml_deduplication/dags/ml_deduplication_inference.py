"""DAG that provisions an on-demand Scaleway instance to run ML-deduplication
inference, then terminates it once done.

Lifecycle (create -> wait -> run -> destroy):
  - create : `scw instance server create` with a cloud-init user-data that
             installs Docker and pre-pulls the inference image. Also creates the
             locked-down security group and a flexible IP.
  - wait   : poll until the instance is running and the image is present (SSH).
  - run    : SSH in and `docker run` the inference image, reading acteurs from
             the warehouse DB (a temp table holding the selected acteurs pool)
             and writing clusters/predictions back to tables.
  - destroy: terminate the instance, release the IP and delete the security
             group (always runs, even on failure).

After inference, the clusters produced for the run are selected, joined with
the full acteurs and enriched, then fed to the same parent/suggestion logic as
the clustering DAG to produce suggestions.

All provisioning is done through the scw CLI from the scheduler container; the
instance is ephemeral (one per run) so no declarative Terraform is needed.
"""

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Param, dag
from cluster.config.constants import FIELDS_PARENT_DATA_EXCLUDED, UNNORMALIZABLE_FIELDS
from cluster.ui import params_separators as UI_PARAMS_SEPARATORS
from decouple import config
from ml_deduplication.config.tasks import TASKS
from ml_deduplication.tasks.airflow_logic.chain_tasks import chain_tasks
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from utils.airflow_params import airflow_params_dropdown_from_mapping
from utils.webapp import (
    get_acteur_columns_from_webapp,
    get_acteur_types_from_webapp,
    get_sources_from_webapp,
)

DAG_ID = "ml_deduplication_inference"
SCRIPTS = "/opt/airflow/scripts/infrastructure"

# SSH keys are injected as container env (like SCW_*, DB_WAREHOUSE):
# ML_DEDUPLICATION_SSH_PUB_KEY (public, injected into the instance via the
# AUTHORIZED_KEY= server tag at creation) and ML_DEDUPLICATION_SSH_KEY_B64
# (base64-encoded private key, decoded to a temp file by the scripts to SSH in).
# The scripts also accept ML_DEDUPLICATION_SSH_KEY as a pre-placed key file path.

ENVIRONMENT = config("ENVIRONMENT", default="development")

# Inference image registry namespace, per environment. CI pushes preprod images
# to ns-ml-deduplication-inference-preprod and prod images (main) to
# ns-ml-deduplication-inference-prod (see
# .github/workflows/ml-deduplication-inference-build-and-push.yml).
IMAGE_NAMESPACE = (
    "ns-ml-deduplication-inference-preprod"
    if ENVIRONMENT == "preprod"
    else "ns-ml-deduplication-inference-prod"
)

# Default to the latest image published for the current environment.
DEFAULT_IMAGE = f"rg.fr-par.scw.cloud/{IMAGE_NAMESPACE}/ml-deduplication-inference:latest"  # noqa: E501

# When set to 1/true, the DAG bypasses the on-demand Scaleway instance and runs
# the inference image directly with docker (requires the docker CLI/socket to be
# reachable where the DAG executes, e.g. inside the local scheduler container
# when the docker socket is mounted). Defaults from env so local dev can opt in.
RUN_LOCAL = config("ML_DEDUPLICATION_RUN_LOCAL", default=False, cast=bool)

# When set to 1/true, the inference container is granted access to an NVIDIA GPU
# (docker run --gpus) and the SentenceTransformer embedding model runs on CUDA.
# The inference image is CUDA-based (torch cu13 wheels) and the instance type is
# GPU-capable, so this can be enabled per environment. Defaults from env.
USE_GPU = config("ML_DEDUPLICATION_USE_GPU", default=True, cast=bool)

# Create dropdowns
mapping_source_id_by_code = {
    source["code"]: source["id"] for source in get_sources_from_webapp()
}
mapping_acteur_type_id_by_code = {
    acteur_type["code"]: acteur_type["id"]
    for acteur_type in get_acteur_types_from_webapp()
}
dropdown_sources = airflow_params_dropdown_from_mapping(mapping_source_id_by_code)
dropdown_acteur_types = airflow_params_dropdown_from_mapping(
    mapping_acteur_type_id_by_code
)

acteur_columns = get_acteur_columns_from_webapp()
fields_vue_acteur = acteur_columns["vue_acteur"]
fields_revision_acteur = acteur_columns["revision_acteur"]

fields_all = sorted(
    list(set(fields_vue_acteur["with_properties"]) - set(UNNORMALIZABLE_FIELDS))
)

# intersection of RevisionActeur and VueActeur fields
# because VueActeur is the source and RevisionActeur is the target
fields_enrich = sorted(
    list(
        set(fields_vue_acteur["db_only"])
        & set(fields_revision_acteur["db_only"])
        # Exclude some fields based on business rules (ex: source)
        - set(FIELDS_PARENT_DATA_EXCLUDED)
    )
)
fields_enrich_excluded = list(set(fields_all) - set(fields_enrich))

# To display protected fields in UI without breaking it
# (Airflow UI doesn't wrap, it creates a long line which messes up inputs)
fields_enrich_excluded_ui = [
    fields_enrich_excluded[i : i + 5] for i in range(0, len(fields_enrich_excluded), 5)
]
exclus_string = "  \n".join([", ".join(chunck) for chunck in fields_enrich_excluded_ui])

PARAMS = {
    "dry_run": Param(
        False,
        type="boolean",
        description_md=f"""
                🚱 Si coché, aucune tâche d'écriture ne sera effectuée.
                Ceci permet de tester le DAG rapidement sans peur de
                casser quoi que ce soit (itérer plus vite)
                (ex: pas d'écriture des suggestions en DB,
                donc pas visible dans Django Admin).
                {UI_PARAMS_SEPARATORS.READ_ACTEURS}""",
    ),
    # TODO: permettre de ne sélectionner aucune source = toutes les sources
    "include_sources": Param(
        [],
        type=["null", "array"],
        # La terminologie Airflow n'est pas très heureuse
        # mais "examples" est bien la façon de faire des dropdowns
        # voir https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
        examples=dropdown_sources,
        description_md="""**➕ INCLUSION ACTEURS**: seuls ceux qui proviennent
                de ces sources (opérateur **OU/OR**)

                💯 Si aucune valeur spécifiée =  tous les acteurs sont inclus
                """,
    ),
    "include_acteur_types": Param(
        [],
        type="array",
        examples=dropdown_acteur_types,
        description_md="""**➕ INCLUSION ACTEURS**: ceux qui sont de ces types
                 (opérateur **OU/OR**)""",
    ),
    "dedup_enrich_fields": Param(
        fields_enrich,
        type=["array"],
        examples=fields_enrich,
        description_md=f"""✍️ Champs à enrichir (certains champs de type calculés ou id
            sont exclus)

            Exclus:
            {exclus_string}
            """,
    ),
    "dedup_enrich_exclude_sources": Param(
        [],
        type=["null", "array"],
        examples=dropdown_sources,
        description_md="""**❌ EXCLUSIONS SOURCES**: sources sur lesquelles
                ne **JAMAIS** prendre de données""",
    ),
    "dedup_enrich_priority_sources": Param(
        [],
        type=["array"],
        examples=dropdown_sources,
        description_md=r"""**🔢 PRIORITES SOURCES**: sources sur lesquelles
                on **PRÉFÈRE** prendre de données

                🔴 BUG UI AIRFLOW: ne sélectionner qu'une valeur car l'ordre
                n'est pas garanti 🔴
                voir https://github.com/apache/airflow/discussions/46475

                Ce n'est pas parce qu'une source est prioritaire qu'on va
                nécessairement en tirer de la donnée
                """,
    ),
    "dedup_enrich_keep_empty": Param(
        False,
        type="boolean",
        description_md=r"""**∅ CONSERVER LE VIDE**: si OUI et qu'une valeur
            vide est rencontrée sur une source prioritaire, alors elle sera
            conservée.
            **Cette option n'est appliquée que lors de la mis à jour du parent**""",
    ),
    "dedup_enrich_keep_parent_data_by_default": Param(
        True,
        type="boolean",
        description_md=r"""
    ** CONSERVER LES DONNÉES DU PARENT**: si OUI, les données du
    parent seront conservées.

    Dans le cas de la mise à jour du parent, lorsque l'option
    `dedup_enrich_keep_empty` est:
     - VRAI, toutes les données du parent même vides sont conservées
     - FAUX, seules les données non-vides du parent sont conservées
    """,
    ),
    "acteurs_table": Param(
        None,
        type=["null", "string"],
        description_md="""Table/view name to read acteurs from in the warehouse DB
            (e.g. `qfdmo_vueacteur`). When empty (recommended), a temp table holding
            the selected acteurs pool is created automatically from the selection
            params and passed to the inference.""",
    ),
    "output_table": Param(
        "public.ml_deduplication",
        type="string",
        description_md="""Base name of the DB table(s) to upload results to, in the
            `public` schema of the warehouse DB. Clusters go to
            `<output_table>_clusters`, candidate pairs to
            `<output_table>_predictions`. Required for the post-inference
            suggestion logic.""",
    ),
    "image_ref": Param(
        DEFAULT_IMAGE,
        type="string",
        description_md="Inference image reference to pull and run.",
    ),
    "run_locally": Param(
        RUN_LOCAL,
        type="boolean",
        description_md=(
            "🐳 Si coché, on **n'utilise PAS d'instance Scaleway** : l'inférence "
            "tourne localement avec docker (`docker run` de l'image d'inférence) "
            "sur le poste où s'exécute le DAG. Nécessite docker (socket monté dans "
            "le conteneur scheduler en local) et un accès au warehouse DB. "
            "Idéal pour tester le DAG localement (via `dag.test`)."
        ),
    ),
    "limit_acteurs": Param(
        None,
        type=["null", "integer"],
        description_md="""🔢 **LIMITE ACTEURS**: nombre maximal d'acteurs à sélectionner
            (LIMIT SQL sur le pool donné à l'inférence). Laisser vide pour tout
            traiter. Utile pour tester rapidement sur un petit échantillon.""",
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
    "use_gpu": Param(
        USE_GPU,
        type="boolean",
        description_md=(
            "Run the SentenceTransformer embedding model on the NVIDIA GPU of the "
            "inference instance (docker run --gpus + --device cuda)."
        ),
    ),
    "duckdb_memory_limit": Param(
        "24GB",
        type=["null", "string"],
        description_md=(
            "Mémoire maximale à utiliser pour la partie blocking de l'inférence."
        ),
    ),
    "skip_cleanup": Param(
        False,
        type="boolean",
        description_md=(
            "🧹 **IGNORER LE NETTOYAGE**: si coché, la table temporaire du pool "
            "d'acteurs n'est **PAS supprimée** à la fin du run, pour pouvoir "
            "l'inspecter en debug. ⚠️ Ne pas laisser coché en production "
            "(risque d'accumulation de tables temporaires)."
        ),
    ),
}


@dag(
    dag_id=DAG_ID,
    dag_display_name="ML - Deduplication - Inference",
    schedule=None,
    start_date=START_DATES.DEFAULT,
    is_paused_upon_creation=False,
    max_active_runs=1,
    catchup=False,
    tags=[TAGS.ML, TAGS.DEDUPLICATION, TAGS.SCALEWAY],
    params=PARAMS,
)
def ml_deduplication_inference():
    # run_id / output_table / acteurs_table are read from XCom (pushed by the
    # config_create and acteurs_select tasks) via Jinja. The `env` dict of a
    # BashOperator is Jinja-templated at execution time, so these resolve to
    # the values produced by the upstream tasks of this run.
    env = {
        "ML_DEDUPLICATION_ACTEURS_TABLE": (
            "{{ ti.xcom_pull(task_ids='"
            + TASKS.SELECTION
            + "', key='acteurs_view') or params.acteurs_table or '' }}"
        ),
        "ML_DEDUPLICATION_OUTPUT_TABLE": "{{ params.output_table }}",
        "ML_DEDUPLICATION_RUN_ID": (
            "{{ ti.xcom_pull(task_ids='" + TASKS.CONFIG_CREATE + "', key='run_id') }}"
        ),
        "ML_DEDUPLICATION_IMAGE": "{{ params.image_ref }}",
        "ML_DEDUPLICATION_MODEL_THRESHOLD": "{{ params.model_threshold or '' }}",
        "ML_DEDUPLICATION_LINKAGE_COLUMN": "{{ params.linkage_column or '' }}",
        "ML_DEDUPLICATION_SPLIT_BY_DEPARTEMENT": (
            "{{ '1' if params.split_by_departement else '0' }}"
        ),
        # Local mode: when "1"/"true", create/wait/destroy become no-ops and
        # run_inference runs the image locally with docker instead of on a
        # Scaleway instance.
        "ML_DEDUPLICATION_RUN_LOCAL": "{{ '1' if params.run_locally else '0' }}",
        # GPU: when "1"/"true", run_inference passes --gpus + --device cuda so the
        # SentenceTransformer runs on the NVIDIA GPU of the instance.
        "ML_DEDUPLICATION_USE_GPU": "{{ '1' if params.use_gpu else '0' }}",
        # Zone chosen by create_instance (pushed as XCom from its stdout) where
        # the Scaleway instance was created, so wait/run/destroy query the same
        # zone. Falls back to the script default when not set (e.g. local mode).
        "ML_DEDUPLICATION_ZONE": (
            "{{ ti.xcom_pull(task_ids='" + TASKS.CREATE_INSTANCE + "') or '' }}"
        ),
        "DUCKDB_MEMORY_LIMIT": "{{ params.duckdb_memory_limit }}",
    }

    instance_ops = {
        "create_instance": BashOperator(
            task_id=TASKS.CREATE_INSTANCE,
            bash_command=f"{SCRIPTS}/ml_deduplication_instance_create.sh ",
            env=env,
            append_env=True,
        ),
        "wait_for_ready": BashOperator(
            task_id=TASKS.WAIT_FOR_READY,
            bash_command=f"{SCRIPTS}/ml_deduplication_instance_wait.sh ",
            env=env,
            append_env=True,
        ),
        "run_inference": BashOperator(
            task_id=TASKS.RUN_INFERENCE,
            bash_command=f"{SCRIPTS}/ml_deduplication_inference_run.sh ",
            env=env,
            append_env=True,
        ),
        # Always clean up, whether or not upstream tasks succeeded.
        "destroy_instance": BashOperator(
            task_id=TASKS.DESTROY_INSTANCE,
            bash_command=f"{SCRIPTS}/ml_deduplication_instance_destroy.sh ",
            env=env,
            trigger_rule="all_done",
            append_env=True,
        ),
    }

    chain_tasks(
        fields_all=[
            "nom",
            "identifiant_unique",
            "acteur_type_id",
            "adresse",
            "adresse_complement",
            "code_postal",
            "code_commune_insee",
            "ville",
            "telephone",
            "nom_commercial",
            "nom_officiel",
            "siren",
            "siret",
            "latitude",
            "longitude",
            "source_id",
            "parent_id",
        ],
        instance_ops=instance_ops,
    )


ml_deduplication_inference_dag = ml_deduplication_inference()

if __name__ == "__main__":
    ml_deduplication_inference_dag.test(
        run_conf={
            "dry_run": False,
            "image_ref": DEFAULT_IMAGE,
            "output_table": "ml_deduplication",
            "acteurs_table": None,
            "linkage_column": None,
            "include_sources": [],
            "model_threshold": None,
            "dedup_enrich_fields": [
                "acteur_type",
                "action_principale",
                "adresse",
                "adresse_complement",
                "code_postal",
                "commentaires",
                "consignes_dacces",
                "description",
                "email",
                "exclusivite_de_reprisereparation",
                "horaires_description",
                "horaires_osm",
                "location",
                "naf_principal",
                "nom",
                "nom_commercial",
                "nom_officiel",
                "public_accueilli",
                "reprise",
                "siren",
                "siret",
                "siret_is_closed",
                "telephone",
                "uniquement_sur_rdv",
                "url",
                "ville",
            ],
            "include_acteur_types": ["commerce (id=4)", "artisan (id=3)"],
            "split_by_departement": False,
            "dedup_enrich_keep_empty": False,
            "dedup_enrich_exclude_sources": [],
            "dedup_enrich_priority_sources": [],
            "dedup_enrich_keep_parent_data_by_default": True,
            "run_locally": False,
            "limit_acteurs": 60000,
        }
    )
