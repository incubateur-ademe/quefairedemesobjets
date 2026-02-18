from unittest.mock import MagicMock, Mock, patch

from acteurs.tasks.business_logic.copy_db_data import copy_db_data


class TestCopyDbData:
    """Tests unitaires pour la fonction copy_db_data avec mocks"""

    @patch("importlib.import_module")
    @patch("acteurs.tasks.business_logic.copy_db_data.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_data_filters_tables_correctly(
        self,
        mock_settings,
        mock_connections,
        mock_dump_and_restore_db,
        mock_import_module,
    ):
        """
        Test that the function filters tables correctly according
        to INSTALLED_APPS and EXCLUDE_TABLES
        """
        # Mock settings
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        # Mock the imported core.settings module
        mock_main_settings = Mock()
        mock_main_settings.INSTALLED_APPS = ["qfdmo", "qfdmd", "data", "core"]
        mock_import_module.return_value = mock_main_settings

        # Mock cursor and its SQL execution
        mock_cursor = MagicMock()
        # Simulate tables from different sources
        mock_cursor.fetchall.return_value = [
            ("qfdmo_acteur",),  # Should be excluded
            ("qfdmo_displayedacteur",),  # Should be excluded
            ("qfdmo_sometable",),  # Should be included
            ("data_suggestion",),  # Should be included
            ("core_setting",),  # Should be included
            ("other_table",),  # Does not start with INSTALLED_APPS, should be excluded
            ("qfdmo_acteur_acteur_services",),  # Should be excluded (in EXCLUDE_TABLES)
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        # Execute the function
        copy_db_data()

        # Assertions
        mock_cursor.execute.assert_called_once_with(
            "SELECT table_name FROM information_schema.tables"
        )
        mock_cursor.fetchall.assert_called_once()

        # Assert that dump_and_restore_db was called with the correct tables
        mock_dump_and_restore_db.assert_called_once()
        call_args = mock_dump_and_restore_db.call_args

        assert call_args.kwargs["source_dsn"] == "postgresql://source_db"
        assert call_args.kwargs["dest_dsn"] == "postgresql://dest_db"
        assert call_args.kwargs["data_only"] is True

        # Assert that only valid tables are included
        tables_passed = call_args.kwargs["tables"]
        assert "qfdmo_sometable" in tables_passed
        assert "data_suggestion" in tables_passed
        assert "core_setting" in tables_passed

        # Assert that excluded tables are not present
        assert "qfdmo_acteur" not in tables_passed
        assert "qfdmo_displayedacteur" not in tables_passed
        assert "qfdmo_acteur_acteur_services" not in tables_passed
        assert "other_table" not in tables_passed

    @patch("importlib.import_module")
    @patch("acteurs.tasks.business_logic.copy_db_data.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_data_passes_correct_parameters_to_dump_and_restore(
        self,
        mock_settings,
        mock_connections,
        mock_dump_and_restore_db,
        mock_import_module,
    ):
        """Test that all parameters are correctly passed to dump_and_restore_db"""
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        # Mock the imported core.settings module
        mock_main_settings = Mock()
        mock_main_settings.INSTALLED_APPS = ["qfdmo", "data"]
        mock_import_module.return_value = mock_main_settings

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("qfdmo_valid_table",),
            ("data_valid_table",),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        copy_db_data()

        # Assert that all parameters are correctly passed to dump_and_restore_db
        mock_dump_and_restore_db.assert_called_once_with(
            source_dsn="postgresql://source_db",
            dest_dsn="postgresql://dest_db",
            tables=["qfdmo_valid_table", "data_valid_table"],
            data_only=True,
        )
