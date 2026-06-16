from unittest.mock import MagicMock, patch

from acteurs.tasks.business_logic.copy_db_schema import copy_db_schema


class TestCopyDbSchema:
    """Tests unitaires pour la fonction copy_db_schema avec mocks"""

    @patch("acteurs.tasks.business_logic.copy_db_schema.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_schema_drops_all_tables_and_calls_dump_and_restore(
        self, mock_settings, mock_connections, mock_dump_and_restore_db
    ):
        """
        Test that the function drops all tables and calls dump_and_restore_db
        with schema_only=True
        """
        # Mock settings
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        # Mock cursor and its SQL execution
        mock_cursor = MagicMock()
        # Simulate tables to drop
        mock_cursor.fetchall.return_value = [
            ("table1",),
            ("table2",),
            ("table3",),
        ]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        # Execute the function
        copy_db_schema()

        # Assertions
        # Verify that _get_all_tables query was executed
        mock_cursor.execute.assert_any_call(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """
        )
        mock_cursor.fetchall.assert_called_once()

        # Verify that DROP TABLE was called for each table
        assert mock_cursor.execute.call_count == 4  # 1 SELECT + 3 DROP TABLE
        drop_calls = [
            call[0][0]
            for call in mock_cursor.execute.call_args_list
            if "DROP TABLE" in str(call[0][0])
        ]
        assert 'DROP TABLE IF EXISTS "table1" CASCADE;' in drop_calls
        assert 'DROP TABLE IF EXISTS "table2" CASCADE;' in drop_calls
        assert 'DROP TABLE IF EXISTS "table3" CASCADE;' in drop_calls

        # Verify that dump_and_restore_db was called with correct parameters
        mock_dump_and_restore_db.assert_called_once_with(
            source_dsn="postgresql://source_db",
            dest_dsn="postgresql://dest_db",
            schema_only=True,
        )

    @patch("acteurs.tasks.business_logic.copy_db_schema.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_schema_handles_drop_table_errors(
        self, mock_settings, mock_connections, mock_dump_and_restore_db
    ):
        """
        Test that the function handles errors when dropping tables gracefully
        """
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("table1",),
            ("table2",),
        ]
        # Track calls to execute
        execute_calls = []

        def execute_side_effect(query):
            execute_calls.append(query)
            # Simulate error when dropping table2
            if "DROP TABLE" in query and "table2" in query:
                raise Exception("Permission denied")

        mock_cursor.execute.side_effect = execute_side_effect

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        # Should not raise exception
        copy_db_schema()

        # Verify that dump_and_restore_db was still called despite errors
        mock_dump_and_restore_db.assert_called_once_with(
            source_dsn="postgresql://source_db",
            dest_dsn="postgresql://dest_db",
            schema_only=True,
        )

    @patch("acteurs.tasks.business_logic.copy_db_schema.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_schema_uses_correct_connection(
        self, mock_settings, mock_connections, mock_dump_and_restore_db
    ):
        """
        Test that the function uses the correct database connection
        """
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        copy_db_schema()

        # Verify that the "webapp_sample" connection is used
        mock_connections.__getitem__.assert_called_once_with("webapp_sample")

    @patch("acteurs.tasks.business_logic.copy_db_schema.dump_and_restore_db")
    @patch("django.db.connections")
    @patch("django.conf.settings")
    def test_copy_db_schema_passes_correct_parameters_to_dump_and_restore(
        self, mock_settings, mock_connections, mock_dump_and_restore_db
    ):
        """
        Test that all parameters are correctly passed to dump_and_restore_db
        """
        mock_settings.DATABASE_URL = "postgresql://source_db"
        mock_settings.DB_WEBAPP_SAMPLE = "postgresql://dest_db"

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("test_table",)]

        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection

        copy_db_schema()

        # Verify all parameters
        mock_dump_and_restore_db.assert_called_once_with(
            source_dsn="postgresql://source_db",
            dest_dsn="postgresql://dest_db",
            schema_only=True,
        )
