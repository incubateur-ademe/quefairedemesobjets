"""Build the ML-deduplication config from DAG params + DB data."""

from ml_deduplication.config.models import MLDeduplicationConfig


def ml_deduplication_run_id_generate(dag_run_id: str) -> str:
    """Generate a deterministic run_id for a DAG run.

    The run_id must be shared between:
      - the `run_inference` BashOperator (passed to the inference image and
        written into the <output_table>_clusters/_predictions tables), and
      - the post-inference `clusters_select` task (which filters those tables
        by run_id).

    We build it from the Airflow dag_run id so it's unique per run and stable
    across the run's tasks. The inference table/view name regex only allows
    letters, digits, dots and underscores, so we strip anything else.
    """
    safe = "".join(c for c in dag_run_id if c.isalnum() or c in "_")
    return f"ml_{safe}"


def ml_deduplication_config_create(
    params: dict, dag_run_id: str, fields_all: list[str]
) -> MLDeduplicationConfig:
    """Create config by merging params with extra data from DB."""
    from utils.django import django_setup_full

    django_setup_full()
    from qfdmo.models import ActeurType, Source

    extra = {
        "mapping_sources": {x.code: x.id for x in Source.objects.all()},
        "mapping_acteur_types": {x.code: x.id for x in ActeurType.objects.all()},
        "fields_all": fields_all,
    }
    return MLDeduplicationConfig(**(params | extra))
