import re
from datetime import datetime

import pytest
from clone.tasks.business_logic.clone_table_name_prepare import (
    build_timestamp_from_table_name,
    build_timestamp_is_valid,
    clone_ae_table_names_prepare,
)

from dags.clone.config import SCHEMAS_PREFIX, TABLES


class TestBuildTimestamp:

    def test_is_valid(self):
        assert build_timestamp_is_valid("20220101120000")
        assert not build_timestamp_is_valid("00000000000000")

    def test_extract_from_table_name(self):
        assert build_timestamp_from_table_name("foo_20220101120000") == "20220101120000"
        assert build_timestamp_from_table_name("foo_00000000000000") is None


class TestcopyAeDbTableNamesCreate:

    @pytest.fixture
    def results(self):
        ts_before = datetime.now().strftime("%Y%m%d%H%M%S")
        names = clone_ae_table_names_prepare()
        return names, ts_before

    @pytest.fixture
    def names(self, results):
        return results[0]

    @pytest.fixture
    def ts_before(self, results):
        return results[1]

    def test_dict_contains_both_tables(self, names):
        assert isinstance(names, dict)
        assert TABLES.UNITE.kind in names
        assert TABLES.ETAB.kind in names

    def test_syntax(self, names):
        assert re.fullmatch(
            SCHEMAS_PREFIX + r"_unite_legale_\d{14}", names[TABLES.UNITE.kind]
        )
        assert re.fullmatch(
            SCHEMAS_PREFIX + r"_etablissement_\d{14}", names[TABLES.ETAB.kind]
        )

    def test_timestamps(self, names, ts_before):
        ts_unite_legale = names["unite_legale"][-14:]
        ts_etablissement = names["etablissement"][-14:]
        # Obviously we want valid timestamps
        assert build_timestamp_is_valid(ts_unite_legale)
        assert build_timestamp_is_valid(ts_etablissement)

        # Timestamps should match although technically there
        # won't be created at the exact same time, this is so
        # that they have the same build timestamp
        assert ts_unite_legale == ts_etablissement

        # Timestamp is properly generated on the fly and not
        # inherited from loading the module, so it's as close
        # as possible to actual creation time
        assert ts_before <= ts_unite_legale
        assert ts_before <= ts_etablissement
