from osm.config.models import OSMExtractLoadConfig


def osm_extract_load_config_create(params: dict) -> OSMExtractLoadConfig:
    """Create DAG config."""

    return OSMExtractLoadConfig(**params)
