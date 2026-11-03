from unittest.mock import MagicMock, patch

import pendulum
import pytest
import requests
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_fiches_to_s3 import (
    FICHES_OPENDATA_FILENAMES,
    export_opendata_fiche_to_s3,
)
from acteurs.tasks.business_logic.remove_old_s3_opendata_csv import (
    remove_old_s3_opendata_csv,
)

CONFIG = ExportOpendataConfig(
    bucket_name="lvao-opendata",
    remote_dir="acteurs-test",
    s3_connection_id="s3data",
    opendata_table="exposure_opendata_acteur_published",
    fiches_remote_dir="fiches-test",
)

MODULE = "acteurs.tasks.business_logic.export_opendata_fiches_to_s3"
CLEANUP = "acteurs.tasks.business_logic.remove_old_s3_opendata_csv"


def response(content=b"a,b\n1,2\n", status=200):
    mock = MagicMock(content=content)
    if status >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(str(status))
    return mock


class TestExportOpendataFicheToS3:
    def test_publishes_a_dated_copy_and_the_latest_state(self):
        with (
            patch(f"{MODULE}.requests.get", return_value=response()) as get,
            patch(f"{MODULE}.S3Hook") as hook_class,
            patch(
                f"{MODULE}.pendulum.now",
                return_value=pendulum.datetime(2026, 11, 2, 1, 0, 0),
            ),
        ):
            export_opendata_fiche_to_s3(CONFIG, "produits.csv")

        assert get.call_args.args[0].endswith("/api/v1/produits")
        assert get.call_args.kwargs["headers"] == {"Accept": "text/csv"}
        dated, latest = hook_class.return_value.load_bytes.call_args_list
        assert dated.kwargs["key"] == "fiches-test/20261102010000_produits.csv"
        assert "acl_policy" not in dated.kwargs
        assert latest.kwargs["key"] == "fiches-test/produits.csv"
        assert latest.kwargs["acl_policy"] == "public-read"

    def test_an_api_error_stops_the_export_before_any_upload(self):
        with (
            patch(f"{MODULE}.requests.get", return_value=response(status=500)),
            patch(f"{MODULE}.S3Hook") as hook_class,
            pytest.raises(requests.HTTPError),
        ):
            export_opendata_fiche_to_s3(CONFIG, "consignes.csv")

        hook_class.return_value.load_bytes.assert_not_called()


class TestRemoveOldFiches:
    def test_keeps_the_latest_state_and_removes_old_dated_copies(self):
        with patch(f"{CLEANUP}.S3Hook") as hook_class:
            hook = hook_class.return_value
            hook.list_keys.return_value = [
                "fiches-test/produits.csv",
                "fiches-test/consignes.csv",
                "fiches-test/20260901010000_produits.csv",
                "fiches-test/20260901010000_consignes.csv",
            ]

            remove_old_s3_opendata_csv(
                CONFIG,
                remote_dir="fiches-test",
                kept_filenames=FICHES_OPENDATA_FILENAMES,
            )

        assert hook.list_keys.call_args.kwargs["prefix"] == "fiches-test"
        assert hook.delete_objects.call_args.kwargs["keys"] == [
            "fiches-test/20260901010000_produits.csv",
            "fiches-test/20260901010000_consignes.csv",
        ]

    def test_the_acteurs_cleanup_is_unchanged(self):
        with patch(f"{CLEANUP}.S3Hook") as hook_class:
            hook = hook_class.return_value
            hook.list_keys.return_value = [
                "acteurs-test/acteurs.csv",
                "acteurs-test/20260901010000.csv",
            ]

            remove_old_s3_opendata_csv(CONFIG)

        assert hook.list_keys.call_args.kwargs["prefix"] == "acteurs-test"
        assert hook.delete_objects.call_args.kwargs["keys"] == [
            "acteurs-test/20260901010000.csv"
        ]
