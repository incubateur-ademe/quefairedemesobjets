from pathlib import Path
from unittest.mock import patch

import pytest
from clone.config.models import CloneConfig
from clone.tasks.business_logic.fix_corrupted_utf8 import (
    UnsafeSedSubstitutionError,
    fix_corrupted_utf8_file,
    validate_sed_substitutions,
)
from pydantic import ValidationError


class TestValidateSedSubstitution:

    @pytest.mark.parametrize(
        "expression",
        [
            ["s/entr\xef\xbf\xbd\xa9e/entrée/"],
            ["s/foo/bar/"],
            ["s/foo/bar/g"],
            ["s/entr\xef\xbf\xbd\xa9e/entrée/", "s/foo/bar/g"],
        ],
    )
    def test_accepts_safe_expressions(self, expression):
        validate_sed_substitutions(expression)

    @pytest.mark.parametrize(
        "expression",
        [
            [""],
            ["s/foo/bar"],
            ["s/foo/bar/; rm -rf /"],
            ["s/foo/bar/e"],
            ["s/foo/bar/w /etc/passwd"],
            ["s/$(whoami)/bar/"],
            ["12086494s/entr\xef\xbf\xbd\xa9e/entrée/"],
            ["s/a'b/bar/"],
            ["s/a/b/", "s/foo/bar"],
        ],
    )
    def test_rejects_unsafe_expressions(self, expression):
        with pytest.raises(UnsafeSedSubstitutionError):
            validate_sed_substitutions(expression)


class TestFixCorruptedUtf8File:

    def test_quotes_sed_expression_for_shell(self, tmp_path: Path):
        csv_file = tmp_path / "sample.csv"
        csv_file.write_bytes(b"content\n")

        with patch(
            "clone.tasks.business_logic.fix_corrupted_utf8.cmd_run"
        ) as mock_cmd_run:
            fix_corrupted_utf8_file(
                file_path=csv_file,
                sed_substitutions=[r"s/\xef\xbf\xbd\xa9/é/"],
            )

        mock_cmd_run.assert_called_once_with(
            f"sed -i 's/\\xef\\xbf\\xbd\\xa9/é/' {csv_file}",
            dry_run=False,
        )

    def test_ignores_empty_substitutions(self, tmp_path: Path):
        csv_file = tmp_path / "sample.csv"
        csv_file.write_bytes(b"content\n")

        with patch(
            "clone.tasks.business_logic.fix_corrupted_utf8.cmd_run"
        ) as mock_cmd_run:
            fix_corrupted_utf8_file(
                file_path=csv_file,
                sed_substitutions=["", "  "],
            )

        mock_cmd_run.assert_not_called()


class TestCloneConfigValidation:

    def test_allows_empty_substitutions(self):
        config = CloneConfig(
            dry_run=False,
            table_kind="my_table",
            data_endpoint="https://example.org/data.csv",  # type: ignore
            run_timestamp="20220305120000",
            fix_corrupted_utf8_sed_substitutions=[],
        )
        assert config.fix_corrupted_utf8_sed_substitutions == []

    def test_validates_each_substitution(self):
        config = CloneConfig(
            dry_run=False,
            table_kind="my_table",
            data_endpoint="https://example.org/data.csv",  # type: ignore
            run_timestamp="20220305120000",
            fix_corrupted_utf8_sed_substitutions=[
                r"s/entr\xef\xbf\xbd\xa9e/entrée/g",
                r"s/foo/bar/",
            ],
        )
        assert len(config.fix_corrupted_utf8_sed_substitutions) == 2

    def test_rejects_unsafe_substitution(self):
        with pytest.raises(ValidationError):
            CloneConfig(
                dry_run=False,
                table_kind="my_table",
                data_endpoint="https://example.org/data.csv",  # type: ignore
                run_timestamp="20220305120000",
                fix_corrupted_utf8_sed_substitutions=["s/a/b/; rm -rf /"],
            )
