"""Tests for the OSM Extract and Load DAG configuration model."""

import pytest
from pydantic import ValidationError

from osm.config.models import OSMExtractLoadConfig

DATASET_URL = "https://download.geofabrik.de/europe/france/france-latest.osm.pbf"


class TestOSMExtractLoadConfig:

    def test_valid_config_builds(self):
        config = OSMExtractLoadConfig(
            dry_run=False,
            osm_dataset_url=DATASET_URL,
        )
        assert config.dry_run is False
        assert str(config.osm_dataset_url) == DATASET_URL

    def test_dry_run_false_is_accepted(self):
        config = OSMExtractLoadConfig(
            dry_run=False,
            osm_dataset_url=DATASET_URL,
        )
        assert config.dry_run is False

    def test_dry_run_none_raises(self):
        # On veut forcer l'init du dry_run pour limiter
        # les risques de faux positifs (ex: valeur None
        # qui fait échouer if config.dry_run et entraine
        # des modifications)
        with pytest.raises(ValueError, match="dry_run à fournir"):
            OSMExtractLoadConfig(
                dry_run=None,
                osm_dataset_url=DATASET_URL,
            )

    def test_invalid_url_raises(self):
        with pytest.raises(ValidationError):
            OSMExtractLoadConfig(
                dry_run=True,
                osm_dataset_url="pas une url",
            )
