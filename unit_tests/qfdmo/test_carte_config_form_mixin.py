import pytest
from django import forms

from core.exceptions import (
    CarteConfigChoicesMappingError,
    CarteConfigInitialMappingError,
)
from qfdmo.mixins import CarteConfigFormMixin
from qfdmo.models import CarteConfig
from qfdmo.models.acteur import LabelQualite
from qfdmo.models.action import GroupeAction
from unit_tests.qfdmo.acteur_factory import LabelQualiteFactory
from unit_tests.qfdmo.action_factory import GroupeActionFactory


class SampleTestForm(CarteConfigFormMixin, forms.Form):
    """Test form with both choices and initial mappings"""

    carte_config_choices_mapping = {
        "groupe_action": "groupe_action",
        "label_qualite": "label_qualite",
    }

    carte_config_initial_mapping = {
        "mode": "mode_affichage",
    }

    groupe_action = forms.ModelMultipleChoiceField(
        queryset=GroupeAction.objects.all(),
        required=False,
    )

    label_qualite = forms.ModelMultipleChoiceField(
        queryset=LabelQualite.objects.all(),
        required=False,
    )

    mode = forms.ChoiceField(
        choices=[
            ("carte", "Carte"),
            ("liste", "Liste"),
        ],
        initial="carte",
        required=False,
    )


@pytest.mark.django_db
class TestCarteConfigFormMixin:
    @pytest.fixture
    def groupe_actions(self):
        """Create test GroupeAction instances"""
        return [
            GroupeActionFactory(code=f"action_{i}", afficher=True) for i in range(5)
        ]

    @pytest.fixture
    def label_qualites(self):
        """Create test LabelQualite instances"""
        return [LabelQualiteFactory(code=f"label_{i}", afficher=True) for i in range(5)]

    @pytest.fixture
    def carte_config(self, groupe_actions, label_qualites):
        """Create a CarteConfig with some ManyToMany relations"""
        config = CarteConfig.objects.create(
            nom="Test Config",
            slug="test-config",
            mode_affichage="liste",
        )
        # Add only first 3 groupe_actions
        config.groupe_action.set(groupe_actions[:3])
        # Add only first 2 label_qualites
        config.label_qualite.set(label_qualites[:2])
        return config

    def test_constructor_with_carte_config(self, carte_config, groupe_actions):
        """Test that passing carte_config to constructor applies overrides
        automatically"""
        form = SampleTestForm(carte_config=carte_config)

        # Overrides should be applied automatically
        assert form.fields["groupe_action"].queryset.count() == 3
        assert form.fields["label_qualite"].queryset.count() == 2
        assert form.fields["mode"].initial == "liste"

    def test_constructor_with_none_carte_config(self, groupe_actions):
        """Test that passing None or omitting carte_config works correctly"""
        # Without carte_config parameter
        form1 = SampleTestForm()
        initial_count1 = form1.fields["groupe_action"].queryset.count()

        # With carte_config=None
        form2 = SampleTestForm(carte_config=None)
        initial_count2 = form2.fields["groupe_action"].queryset.count()

        # Both should have the same (unfiltered) count
        assert initial_count1 == initial_count2
        assert form2.fields["mode"].initial == "carte"

    def test_apply_carte_config_overrides_with_none(self, groupe_actions):
        """Test that applying None carte_config doesn't change the form"""
        form = SampleTestForm()

        # Get initial queryset count
        initial_count = form.fields["groupe_action"].queryset.count()

        # Apply with None
        result = form.apply_carte_config_overrides(None)

        # Should return self
        assert result is form

        # Queryset should be unchanged
        assert form.fields["groupe_action"].queryset.count() == initial_count

    def test_override_choices_filters_queryset(
        self, carte_config, groupe_actions, label_qualites
    ):
        """Test that choices override correctly filters the queryset"""
        form = SampleTestForm()

        # Before override - should have at least the test items
        initial_groupe_action_count = form.fields["groupe_action"].queryset.count()
        initial_label_qualite_count = form.fields["label_qualite"].queryset.count()

        # Verify test items exist in queryset
        assert initial_groupe_action_count >= len(groupe_actions)
        assert initial_label_qualite_count >= len(label_qualites)

        # Apply overrides
        form.apply_carte_config_overrides(carte_config)

        # After override - should only have items from carte_config
        assert form.fields["groupe_action"].queryset.count() == 3
        assert form.fields["label_qualite"].queryset.count() == 2

        # Check that the correct items are in the queryset
        groupe_action_ids = list(
            form.fields["groupe_action"].queryset.values_list("id", flat=True)
        )
        expected_ids = [ga.id for ga in groupe_actions[:3]]
        assert set(groupe_action_ids) == set(expected_ids)

    def test_override_initial_value(self, carte_config):
        """Test that initial value override works correctly"""
        form = SampleTestForm()

        # Before override
        assert form.fields["mode"].initial == "carte"

        # Apply overrides
        form.apply_carte_config_overrides(carte_config)

        # After override - should have value from carte_config
        assert form.fields["mode"].initial == "liste"

    def test_override_with_empty_carte_config_relations(self):
        """Test that empty ManyToMany fields don't override"""
        # Create config without any relations
        config = CarteConfig.objects.create(
            nom="Empty Config",
            slug="empty-config",
            mode_affichage="carte",
        )

        GroupeActionFactory(code="action_1", afficher=True)
        GroupeActionFactory(code="action_2", afficher=True)

        form = SampleTestForm()
        initial_count = form.fields["groupe_action"].queryset.count()

        # Apply overrides
        form.apply_carte_config_overrides(config)

        # Queryset should be unchanged because carte_config has no relations
        assert form.fields["groupe_action"].queryset.count() == initial_count

    def test_override_with_unmapped_fields(self, carte_config):
        """Test that only mapped fields are overridden"""

        class PartialForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {
                "groupe_action": "groupe_action",
                # label_qualite is NOT mapped
            }

            groupe_action = forms.ModelMultipleChoiceField(
                queryset=GroupeAction.objects.all(),
                required=False,
            )

            label_qualite = forms.ModelMultipleChoiceField(
                queryset=LabelQualite.objects.all(),
                required=False,
            )

        form = PartialForm()
        initial_label_count = form.fields["label_qualite"].queryset.count()

        # Apply overrides
        form.apply_carte_config_overrides(carte_config)

        # groupe_action should be filtered
        assert form.fields["groupe_action"].queryset.count() == 3

        # label_qualite should NOT be filtered (not in mapping)
        assert form.fields["label_qualite"].queryset.count() == initial_label_count

    def test_override_with_non_model_choice_field(self):
        """Test that non-ModelChoiceField fields are ignored for choices override"""

        class MixedForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {
                "regular_choice": "groupe_action",  # Wrong type mapping
            }

            regular_choice = forms.ChoiceField(
                choices=[("a", "A"), ("b", "B")],
                required=False,
            )

        config = CarteConfig.objects.create(
            nom="Test", slug="test", mode_affichage="carte"
        )

        form = MixedForm()

        # Should not raise an error
        form.apply_carte_config_overrides(config)

        # Field should be unchanged
        assert len(form.fields["regular_choice"].choices) == 2

    def test_override_with_none_initial_value(self):
        """Test that None or empty initial values don't override"""
        config = CarteConfig.objects.create(
            nom="Test",
            slug="test",
            mode_affichage="carte",  # Use valid value since field is NOT NULL
        )

        form = SampleTestForm()
        original_initial = form.fields["mode"].initial

        # Temporarily set the value to empty string to test empty value handling
        config.mode_affichage = ""

        # Apply overrides
        form.apply_carte_config_overrides(config)

        # Initial should be unchanged because config value is empty string
        assert form.fields["mode"].initial == original_initial

    def test_method_chaining(self, carte_config):
        """Test that apply_carte_config_overrides returns self for chaining"""
        form = SampleTestForm()

        result = form.apply_carte_config_overrides(carte_config)

        assert result is form
        # And verify it actually applied the overrides
        assert form.fields["mode"].initial == "liste"

    def test_override_with_nonexistent_config_field(self):
        """Test that mapping to nonexistent CarteConfig field raises error
        at form instantiation"""

        class BadMappingForm(CarteConfigFormMixin, forms.Form):
            carte_config_initial_mapping = {
                "some_field": "nonexistent_field",
            }

            some_field = forms.CharField(initial="default", required=False)

        # Should raise an error when instantiating the form
        with pytest.raises(CarteConfigInitialMappingError) as exc_info:
            BadMappingForm()

        # Check error message
        error_message = str(exc_info.value)
        assert "BadMappingForm" in error_message
        assert "nonexistent_field" in error_message

    def test_invalid_choices_mapping_raises_error(self):
        """Test that invalid carte_config_choices_mapping raises
        CarteConfigChoicesMappingError"""

        class InvalidChoicesForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {
                "my_field": "nonexistent_field",
            }

            my_field = forms.ModelMultipleChoiceField(
                queryset=GroupeAction.objects.all(),
                required=False,
            )

        with pytest.raises(CarteConfigChoicesMappingError) as exc_info:
            InvalidChoicesForm()

        # Check error message contains helpful information
        error_message = str(exc_info.value)
        assert "InvalidChoicesForm" in error_message
        assert "nonexistent_field" in error_message
        assert "carte_config_choices_mapping" in error_message
        assert "Available fields:" in error_message

    def test_invalid_initial_mapping_raises_error(self):
        """Test that invalid carte_config_initial_mapping raises
        CarteConfigInitialMappingError"""

        class InvalidInitialForm(CarteConfigFormMixin, forms.Form):
            carte_config_initial_mapping = {
                "my_field": "invalid_field",
            }

            my_field = forms.CharField(required=False)

        with pytest.raises(CarteConfigInitialMappingError) as exc_info:
            InvalidInitialForm()

        # Check error message contains helpful information
        error_message = str(exc_info.value)
        assert "InvalidInitialForm" in error_message
        assert "invalid_field" in error_message
        assert "carte_config_initial_mapping" in error_message
        assert "Available fields:" in error_message

    def test_multiple_invalid_fields_in_mapping(self):
        """Test that multiple invalid fields are all reported"""

        class MultipleInvalidForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {
                "field1": "invalid_field_1",
                "field2": "invalid_field_2",
            }

            field1 = forms.ModelMultipleChoiceField(
                queryset=GroupeAction.objects.all(),
                required=False,
            )
            field2 = forms.ModelMultipleChoiceField(
                queryset=LabelQualite.objects.all(),
                required=False,
            )

        with pytest.raises(CarteConfigChoicesMappingError) as exc_info:
            MultipleInvalidForm()

        error_message = str(exc_info.value)
        assert "invalid_field_1" in error_message
        assert "invalid_field_2" in error_message

    def test_valid_mappings_do_not_raise_error(self):
        """Test that valid mappings do not raise any errors"""

        # Should not raise any exception
        class ValidForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {
                "groupe_action": "groupe_action",
            }

            carte_config_initial_mapping = {
                "mode": "mode_affichage",
            }

            groupe_action = forms.ModelMultipleChoiceField(
                queryset=GroupeAction.objects.all(),
                required=False,
            )

            mode = forms.ChoiceField(
                choices=[("carte", "Carte"), ("liste", "Liste")],
                required=False,
            )

        # If we got here, no exception was raised
        form = ValidForm()
        assert form is not None

    def test_empty_mappings_do_not_raise_error(self):
        """Test that empty mappings do not raise any errors"""

        # Should not raise any exception
        class EmptyMappingsForm(CarteConfigFormMixin, forms.Form):
            carte_config_choices_mapping = {}
            carte_config_initial_mapping = {}

            some_field = forms.CharField(required=False)

        form = EmptyMappingsForm()
        assert form is not None
