"""Tests for the FormulaireSynonymeAutocompleteInput widget rendering.

The formulaire object combobox must implement the W3C APG combobox-autocomplete-list
pattern (RGAA 7.1, 7.3, 11.10). These tests assert the HTML output carries the
right ARIA roles and Stimulus targets so the formulaire can drive the search.
"""

import pytest

from qfdmo.forms import FormulaireForm


@pytest.mark.django_db
class TestFormulaireSynonymeAutocompleteInputRendering:
    def setup_method(self):
        self.form = FormulaireForm()
        self.objet_html = str(self.form["sous_categorie_objet"])
        self.sc_id_html = str(self.form["sc_id"])

    def test_combobox_role(self):
        assert 'role="combobox"' in self.objet_html

    def test_aria_controls_points_to_listbox(self):
        assert 'aria-controls="' in self.objet_html
        assert '-listbox"' in self.objet_html

    def test_aria_expanded_initial_state(self):
        assert 'aria-expanded="false"' in self.objet_html

    def test_aria_autocomplete_both(self):
        assert 'aria-autocomplete="both"' in self.objet_html

    def test_listbox_role_on_results_ul(self):
        assert 'role="listbox"' in self.objet_html

    def test_input_target_for_formulaire_controller(self):
        assert 'data-formulaire-synonyme-autocomplete-target="input"' in self.objet_html

    def test_endpoint_url_uses_namespaced_view(self):
        assert (
            "data-next-autocomplete-endpoint-url-value="
            '"/qfdmo/autocomplete/synonyme-formulaire"' in self.objet_html
        )

    def test_sc_id_hidden_input_targets_formulaire_controller(self):
        assert 'data-formulaire-synonyme-autocomplete-target="scId"' in self.sc_id_html
