"""Tests for the CarteAddressAutocompleteInput widget rendering.

The carte address combobox must implement the W3C APG combobox-autocomplete-list
pattern for RGAA criteria 7.1, 7.3 and 11.10. These tests assert the HTML output
carries the right ARIA roles, attributes and Stimulus targets.
"""

import pytest

from qfdmo.forms import MapForm


@pytest.mark.django_db
class TestCarteAddressAutocompleteInputRendering:
    def setup_method(self):
        self.form = MapForm()
        self.adresse_html = str(self.form["adresse"])
        self.latitude_html = str(self.form["latitude"])
        self.longitude_html = str(self.form["longitude"])

    def test_combobox_role(self):
        assert 'role="combobox"' in self.adresse_html

    def test_aria_controls_points_to_listbox(self):
        assert 'aria-controls="' in self.adresse_html
        assert '-listbox"' in self.adresse_html

    def test_aria_expanded_initial_state(self):
        assert 'aria-expanded="false"' in self.adresse_html

    def test_aria_activedescendant_present(self):
        assert "aria-activedescendant" in self.adresse_html

    def test_aria_autocomplete_both(self):
        assert 'aria-autocomplete="both"' in self.adresse_html

    def test_listbox_role_on_results_ul(self):
        assert 'role="listbox"' in self.adresse_html

    def test_input_target_for_carte_controller(self):
        assert 'data-carte-address-autocomplete-target="input"' in self.adresse_html

    def test_input_target_for_next_autocomplete(self):
        assert 'data-next-autocomplete-target="input"' in self.adresse_html

    def test_show_on_focus_enabled(self):
        assert 'data-next-autocomplete-show-on-focus-value="true"' in self.adresse_html

    def test_endpoint_url_uses_namespaced_view(self):
        assert (
            'data-next-autocomplete-endpoint-url-value="/qfdmo/autocomplete/address"'
            in self.adresse_html
        )

    def test_latitude_hidden_input_targets_carte_controller(self):
        assert 'data-carte-address-autocomplete-target="latitude"' in self.latitude_html

    def test_longitude_hidden_input_targets_carte_controller(self):
        assert (
            'data-carte-address-autocomplete-target="longitude"' in self.longitude_html
        )

    def test_no_legacy_address_autocomplete_target(self):
        # Latitude/longitude hidden inputs must not still target the legacy controller.
        assert "data-address-autocomplete-target" not in self.latitude_html
        assert "data-address-autocomplete-target" not in self.longitude_html
