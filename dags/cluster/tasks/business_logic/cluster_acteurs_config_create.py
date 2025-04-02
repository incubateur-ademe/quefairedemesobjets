from cluster.config import ClusterConfig
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_config_create(params: dict) -> ClusterConfig:
    """Création de la config en fusionnant les params airflow
    et autres valeurs métier / DB."""
    from qfdmo.models import ActeurType, Source

    extra = {
        "mapping_sources": {x.code: x.id for x in Source.objects.all()},
        "mapping_acteur_types": {x.code: x.id for x in ActeurType.objects.all()},
    }
    return ClusterConfig(**(params | extra))
