from unittest.mock import MagicMock, patch

import pytest
import requests
from acteurs.tasks.airflow_logic.config_management import ExportOpendataConfig
from acteurs.tasks.business_logic.export_opendata_fiches_to_s3 import (
    export_opendata_fiches_to_s3,
)

CONFIG = ExportOpendataConfig(
    bucket_name="lvao-opendata",
    remote_dir="acteurs-test",
    s3_connection_id="s3data",
    opendata_table="exposure_opendata_acteur_published",
    fiches_remote_dir="fiches-test",
)

MODULE = "acteurs.tasks.business_logic.export_opendata_fiches_to_s3"


def response(content=b"a,b\n1,2\n", status=200):
    mock = MagicMock(content=content)
    if status >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(str(status))
    return mock


class TestExportOpendataFichesToS3:
    def test_publishes_both_files_from_the_api_v1(self):
        with (
            patch(f"{MODULE}.requests.get", return_value=response()) as get,
            patch(f"{MODULE}.S3Hook") as hook_class,
        ):
            export_opendata_fiches_to_s3(CONFIG)

        urls = [call.args[0] for call in get.call_args_list]
        assert [url.split("/api/v1/")[1] for url in urls] == [
            "produits.csv",
            "consignes.csv",
        ]
        load_bytes = hook_class.return_value.load_bytes
        assert [call.kwargs["key"] for call in load_bytes.call_args_list] == [
            "fiches-test/produits.csv",
            "fiches-test/consignes.csv",
        ]
        assert all(
            call.kwargs["bucket_name"] == "lvao-opendata"
            and call.kwargs["replace"] is True
            and call.kwargs["acl_policy"] == "public-read"
            for call in load_bytes.call_args_list
        )

    def test_an_api_error_stops_the_export_before_any_upload(self):
        with (
            patch(f"{MODULE}.requests.get", return_value=response(status=500)),
            patch(f"{MODULE}.S3Hook") as hook_class,
            pytest.raises(requests.HTTPError),
        ):
            export_opendata_fiches_to_s3(CONFIG)

        hook_class.return_value.load_bytes.assert_not_called()
