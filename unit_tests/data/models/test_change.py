import pytest
from pydantic import ValidationError

from data.models.change import SuggestionChange
from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory


@pytest.mark.django_db
class TestSuggestionChange:

    def test_raise_if_order_invalid(self):
        with pytest.raises(
            ValidationError, match="should be greater than or equal to 1"
        ):
            SuggestionChange(
                order=0,  # must be an integer >= 1
                reason="because I want it to break",
                name="sample_model_do_nothing",
                model_params={},
            )

    def test_raise_if_model_name_invalid(self):
        with pytest.raises(ValueError, match="Invalid name"):
            SuggestionChange(
                order=1,
                reason="because I want it to break",
                name="invalid_model_name",
                model_params={},
            )

    def test_raise_if_model_params_invalid(self):
        with pytest.raises(ValidationError, match="identifiant_unique"):
            SuggestionChange(
                order=1,
                reason="because I want it to break",
                name="acteur_change_nothing_in_revision",
                model_params={
                    "FOO": "bar",
                },
            )

    def test_pass_if_all_valid(self):
        RevisionActeurFactory(identifiant_unique="acteur1")
        SuggestionChange(
            order=1,
            reason="because I want it to work",
            name="acteur_change_nothing_in_revision",
            model_params={
                "identifiant_unique": "acteur1",
            },
        )
