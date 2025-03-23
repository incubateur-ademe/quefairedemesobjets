from datetime import datetime

import pytest
from clone.config.model import CloneConfig


class TestCloneConfig:

    @pytest.fixture
    def config(self):
        return CloneConfig(
            dry_run=False,
            table_kind="my_table",
            data_url="https://example.org/data.zip",  # type: ignore
            file_downloaded="data.zip",
            file_unpacked="data.csv",
            run_timestamp="20220305120000",
        )

    def test_run_timestamp(self, config):
        # Is a valid and stable timestamp
        ts = config.run_timestamp
        assert datetime.strptime(ts, "%Y%m%d%H%M%S")
        assert ts == config.run_timestamp
        assert ts == config.run_timestamp

    def test_table_name(self, config):
        assert config.table_name == "clone_my_table_" + config.run_timestamp

    def test_table_name_pattern(self, config):
        assert config.table_name_pattern.match("clone_my_table_20250000000000")

    def test_view_name(self, config):
        assert config.view_name == "clone_my_table_in_use"

    def test_raise_if_paths_dont_exist(self, config):
        with pytest.raises(FileNotFoundError):
            config.validate_paths()
