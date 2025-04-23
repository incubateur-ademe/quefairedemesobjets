import pytest
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    row_to_suggest_data,
)


class TestEnrichSuggestionsRowToSuggestData:

    def test_row_to_suggest_data(self):
        row = {
            "suggest_cohort": "cohort",
            "suggest_siret": "12345678901234",
            "foo": "bar",
        }
        data = row_to_suggest_data(row)
        assert data == {"siret": "12345678901234"}

    @pytest.mark.parametrize(
        "key",
        ["suggest", "suggestion_siret", "siret_suggest"],
    )
    def test_raise_if_inconsistent_suggest_keys(self, key):
        row = {"suggest_cohort": "cohort"}  # must always be present
        row[key] = "12345678901234"
        with pytest.raises(KeyError, match="Colonnes invalides"):
            row_to_suggest_data(row)

    def test_raise_if_missing_cohort(self):
        row = {"suggest_siret": "12345678901234"}
        with pytest.raises(ValueError, match="not in list"):
            row_to_suggest_data(row)
