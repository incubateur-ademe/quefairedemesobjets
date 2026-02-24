import pytest
from pydantic import ValidationError

from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_MODEL_PARAMS,
    COL_CHANGE_NAMESPACE,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
    SuggestionChange,
)
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
                model_name="sample_model_do_nothing",
                model_params={},
            )

    def test_raise_if_model_name_invalid(self):
        with pytest.raises(ValueError, match="Invalid model_name"):
            SuggestionChange(
                order=1,
                reason="because I want it to break",
                model_name="invalid_model_name",
                model_params={},
            )

    def test_raise_if_model_params_invalid(self):
        with pytest.raises(ValidationError, match="id"):
            SuggestionChange(
                order=1,
                reason="because I want it to break",
                model_name="acteur_verify_presence_in_revision",
                model_params={
                    "FOO": "bar",
                },
            )

    def test_pass_if_all_valid(self):
        RevisionActeurFactory(identifiant_unique="acteur1")
        SuggestionChange(
            order=1,
            reason="because I want it to work",
            model_name="acteur_verify_presence_in_revision",
            model_params={
                "id": "acteur1",
            },
        )

    def test_column_constants_are_iso_with_model(self):
        # Ensuring column constants & fields align
        cols_prefixed = set(
            [
                COL_CHANGE_ORDER,
                COL_CHANGE_REASON,
                COL_CHANGE_MODEL_NAME,
                COL_CHANGE_MODEL_PARAMS,
            ]
        )
        # Because constants are meant to be used in other contexts
        # (clutering pipeline), we ensure they are all prefixed
        # with namespace
        assert all(x.startswith(COL_CHANGE_NAMESPACE) for x in cols_prefixed)

        # Without namespace, they should align with the model fields
        cols = set([x.replace(COL_CHANGE_NAMESPACE, "") for x in cols_prefixed])
        fields = set(SuggestionChange.model_fields.keys())
        cols_missing = cols - fields
        fields_missing = fields - cols
        assert not cols_missing, f"Missing columns in model: {cols_missing}"
        assert not fields_missing, f"Missing fields in columns: {fields_missing}"
