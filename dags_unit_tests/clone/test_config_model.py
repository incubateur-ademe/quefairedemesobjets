import pytest
from clone.config.model import DIR_SQL_CREATION, CloneConfig


class TestCloneConfig:

    @pytest.fixture
    def config(self):
        return CloneConfig(
            dry_run=False,
            table_kind="my_table",
            data_endpoint="https://example.org/data.zip",  # type: ignore
            clone_method="download_to_disk_first",
            file_downloaded="data.zip",
            file_unpacked="data.csv",
            delimiter=",",
            run_timestamp="20220305120000",
        )

    def test_table_name(self, config):
        assert config.table_name == "clone_my_table_" + config.run_timestamp

    def test_table_schema_file_path(self, config):
        assert (
            config.table_schema_file_path
            == DIR_SQL_CREATION / "tables" / "create_table_my_table.sql"
        )

    def test_table_name_pattern(self, config):
        pattern = config.table_name_pattern
        assert pattern.match("clone_my_table_20250000000000")
        assert not pattern.match("clone_my_table_20250000000000_other")
        assert not pattern.match("clone_not_my_table_2025000000000")

    def test_view_schema_file_path(self, config):
        assert (
            config.view_schema_file_path
            == DIR_SQL_CREATION / "views" / "create_view_my_table_in_use.sql"
        )

    def test_view_name(self, config):
        assert config.view_name == "clone_my_table_in_use"

    def test_raise_if_paths_dont_exist(self, config):
        with pytest.raises(FileNotFoundError):
            config.validate_paths()
