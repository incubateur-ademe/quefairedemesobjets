from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sources.config.models import SourceConfig
from sources.config.xcoms import XCOMS
from sources.tasks.airflow_logic.source_data_download_task import (
    source_data_download_wrapper,
)
from sources.tasks.airflow_logic.source_data_normalize_task import (
    source_data_normalize_wrapper,
)
from sources.tasks.business_logic.source_data_download import (
    _coerce_legacy_download_dtypes,
    source_data_download,
)
from sources.tasks.business_logic.source_data_normalize import (
    load_acteur_dataframe_at_normalize_start,
)


class TestCoerceLegacyDownloadDtypes:
    def test_casts_numeric_columns_to_str(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = _coerce_legacy_download_dtypes(df)
        assert result["a"].dtype == object or str(result["a"].dtype) == "string"
        assert result["a"].iloc[0] == "1"


class TestSourceDataDownloadStorageFlag:
    @patch(
        "sources.tasks.business_logic.source_data_download.save_source_dataframe_in_warehouse_db"
    )
    @patch(
        "sources.tasks.business_logic.source_data_download.download_source_dataframe"
    )
    def test_warehouse_path_persists_without_legacy_coerce(
        self, mock_download, mock_save
    ):
        raw = pd.DataFrame({"id": [1]})
        mock_download.return_value = raw.copy()

        result = source_data_download(
            endpoint="http://example.com",
            dag_id="test-dag",
            save_datasource_in_warehouse_db=True,
        )

        mock_save.assert_called_once()
        assert result["id"].iloc[0] == 1

    @patch(
        "sources.tasks.business_logic.source_data_download.save_source_dataframe_in_warehouse_db"
    )
    @patch(
        "sources.tasks.business_logic.source_data_download.download_source_dataframe"
    )
    def test_legacy_path_coerces_and_skips_save(self, mock_download, mock_save):
        mock_download.return_value = pd.DataFrame({"id": [1]})

        result = source_data_download(
            endpoint="http://example.com",
            dag_id="test-dag",
            save_datasource_in_warehouse_db=False,
        )

        mock_save.assert_not_called()
        assert result["id"].iloc[0] == "1"


class TestLoadActeurDataframeAtNormalizeStart:
    def test_legacy_path_requires_dataframe(self):
        with pytest.raises(ValueError, match="df_acteur_from_source"):
            load_acteur_dataframe_at_normalize_start(
                dag_id="dag",
                save_datasource_in_warehouse_db=False,
                df_acteur_from_source=None,
            )

    @patch(
        "sources.tasks.business_logic.source_data_normalize.pd.read_sql_table",
    )
    @patch(
        "utils.django.django_conn_to_sqlalchemy_engine",
        return_value=MagicMock(),
    )
    @patch("sources.tasks.business_logic.source_data_normalize.django_setup_full")
    def test_warehouse_path_reads_view(self, _mock_django, _mock_engine, mock_read_sql):
        mock_read_sql.return_value = pd.DataFrame({"x": [1]})
        df = load_acteur_dataframe_at_normalize_start(
            dag_id="eo-refashion",
            save_datasource_in_warehouse_db=True,
        )
        mock_read_sql.assert_called_once()
        assert df["x"].iloc[0] == "1"


class TestAirflowTaskWrappersStorageFlag:
    @patch("sources.tasks.airflow_logic.source_data_download_task.xcom_push")
    @patch("sources.tasks.airflow_logic.source_data_download_task.source_data_download")
    def test_download_pushes_xcom_when_legacy(self, mock_download, mock_xcom_push):
        df = pd.DataFrame({"a": [1]})
        mock_download.return_value = df
        dag = MagicMock(dag_id="cma")
        params = {
            "endpoint": "http://example.com",
            "product_mapping": {},
            "normalization_rules": [],
            "save_datasource_in_warehouse_db": False,
        }

        source_data_download_wrapper(ti=MagicMock(), dag=dag, params=params)

        mock_xcom_push.assert_called_once()
        assert mock_xcom_push.call_args[0][1] == XCOMS.SOURCE_DOWNLOADED

    @patch("sources.tasks.airflow_logic.source_data_download_task.xcom_push")
    @patch("sources.tasks.airflow_logic.source_data_download_task.source_data_download")
    def test_download_skips_xcom_when_warehouse(self, mock_download, mock_xcom_push):
        mock_download.return_value = pd.DataFrame({"a": [1]})
        dag = MagicMock(dag_id="cma")
        params = {
            "endpoint": "http://example.com",
            "product_mapping": {},
            "normalization_rules": [],
            "save_datasource_in_warehouse_db": True,
        }

        source_data_download_wrapper(ti=MagicMock(), dag=dag, params=params)

        mock_xcom_push.assert_not_called()

    @patch("sources.tasks.airflow_logic.source_data_normalize_task.xcom_push")
    @patch(
        "sources.tasks.airflow_logic.source_data_normalize_task.source_data_normalize"
    )
    @patch("sources.tasks.airflow_logic.source_data_normalize_task.xcom_pull")
    def test_normalize_pulls_xcom_when_legacy(
        self, mock_xcom_pull, mock_normalize, _mock_xcom_push
    ):
        pulled = pd.DataFrame({"id": ["1"]})
        mock_xcom_pull.return_value = pulled
        mock_normalize.return_value = (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {},
        )

        params = {
            "endpoint": "http://example.com",
            "product_mapping": {},
            "normalization_rules": [{"keep": "identifiant_unique"}],
            "save_datasource_in_warehouse_db": False,
        }
        source_data_normalize_wrapper(
            ti=MagicMock(), dag=MagicMock(dag_id="cma"), params=params
        )

        mock_xcom_pull.assert_called_once_with(
            mock_xcom_pull.call_args[0][0], XCOMS.SOURCE_DOWNLOADED
        )
        kwargs = mock_normalize.call_args.kwargs
        assert kwargs["save_datasource_in_warehouse_db"] is False
        assert kwargs["df_acteur_from_source"] is pulled

    @patch("sources.tasks.airflow_logic.source_data_normalize_task.xcom_push")
    @patch(
        "sources.tasks.airflow_logic.source_data_normalize_task.source_data_normalize"
    )
    @patch("sources.tasks.airflow_logic.source_data_normalize_task.xcom_pull")
    def test_normalize_skips_xcom_pull_when_warehouse(
        self, mock_xcom_pull, mock_normalize, _mock_xcom_push
    ):
        mock_normalize.return_value = (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            {},
        )

        params = {
            "endpoint": "http://example.com",
            "product_mapping": {},
            "normalization_rules": [{"keep": "identifiant_unique"}],
            "save_datasource_in_warehouse_db": True,
        }
        source_data_normalize_wrapper(
            ti=MagicMock(), dag=MagicMock(dag_id="cma"), params=params
        )

        mock_xcom_pull.assert_not_called()
        assert mock_normalize.call_args.kwargs["df_acteur_from_source"] is None


class TestSourceConfigWarehouseFlag:
    def test_defaults_to_false(self):
        config = SourceConfig.model_validate(
            {
                "endpoint": "http://example.com",
                "product_mapping": {},
                "normalization_rules": [],
            }
        )
        assert config.save_datasource_in_warehouse_db is True
