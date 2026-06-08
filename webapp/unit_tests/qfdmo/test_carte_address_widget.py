"""Tests for CarteAddressAutocompleteInput widget rendering.

The carte address combobox must implement the W3C APG
combobox-autocomplete-list pattern for RGAA criteria 7.1, 7.3, 11.10.
These assertions pin the contract:

- visible <input> carries role=combobox + aria-controls + aria-autocomplete
- Turbo Frame results <ul> carries role=listbox
- the visible input is the only `name=carte_map-adresse` (the fix for the
  duplicate-name resubmit loop) and carries `display_value` correctly
- lat/lng hidden inputs target the carte-address-autocomplete controller
"""

import pytest

from qfdmo.forms import MapForm


@pytest.mark.django_db
class TestCarteAddressAutocompleteInputRendering:
    """The widget is rendered via Django's form helpers, so we instantiate
    MapForm without bound data and inspect the rendered field HTML."""

    def setup_method(self):
        form = MapForm()
        self.adresse_html = str(form["adresse"])
        self.latitude_html = str(form["latitude"])
        self.longitude_html = str(form["longitude"])

    def test_visible_input_has_combobox_role(self):
        assert 'role="combobox"' in self.adresse_html

    def test_visible_input_has_aria_controls_pointing_at_listbox(self):
        assert 'aria-controls="' in self.adresse_html
        assert '-listbox"' in self.adresse_html

    def test_visible_input_starts_with_aria_expanded_false(self):
        assert 'aria-expanded="false"' in self.adresse_html

    def test_visible_input_declares_aria_activedescendant(self):
        # The controller writes the focused option id into this attr on
        # keyboard navigation; it must be present even when empty.
        assert "aria-activedescendant" in self.adresse_html

    def test_visible_input_advertises_list_autocomplete(self):
        # APG combobox-autocomplete-list: aria-autocomplete is "list"
        # (we surface suggestions in the listbox but do NOT inline-complete
        # the typed text — `"both"` would lie to assistive tech).
        assert 'aria-autocomplete="list"' in self.adresse_html
        # Explicitly assert the old value isn't there to flag regressions.
        assert 'aria-autocomplete="both"' not in self.adresse_html

    def test_results_ul_has_listbox_role(self):
        assert 'role="listbox"' in self.adresse_html


@pytest.mark.django_db
class TestCarteAddressAutocompleteInputFormSerialization:
    """Regression: the visible search input used to share its `name` with a
    hidden sibling. The duplicate caused the form to submit two fields with
    the same name; the hidden's empty value won, triggering a resubmit loop.

    Now the visible input IS the form input (carries `name`), and the hidden
    sibling is only rendered when display_value=False (homepage search)."""

    def setup_method(self):
        self.html = str(MapForm()["adresse"])

    def test_visible_input_carries_the_form_name(self):
        # `display_value=True` flips the widget to put `name` on the visible
        # search box so the chosen label is what the form serializes.
        # MapForm's prefix defaults to "map" when no map_container_id is set;
        # the carte template passes "carte" → "carte_map". We assert on the
        # bare-prefix render to stay decoupled from carte view wiring.
        assert 'name="map-adresse"' in self.html

    def test_no_hidden_sibling_input_is_rendered(self):
        # The old structure rendered two inputs with the same name. The fix
        # drops the hidden sibling when display_value is True.
        assert 'type="hidden"' not in self.html
        assert self.html.count('name="map-adresse"') == 1


@pytest.mark.django_db
class TestCarteAddressAutocompleteInputStimulusWiring:
    """Carte-specific Stimulus attributes that bind the widget to the
    `next-autocomplete` controller (combobox engine) and to the outer
    `carte-address-autocomplete` controller (lat/lng + geolocation)."""

    def setup_method(self):
        form = MapForm()
        self.adresse_html = str(form["adresse"])
        self.latitude_html = str(form["latitude"])
        self.longitude_html = str(form["longitude"])

    def test_widget_mounts_next_autocomplete_controller(self):
        assert 'data-controller="next-autocomplete"' in self.adresse_html

    def test_visible_input_targets_next_autocomplete(self):
        assert 'data-next-autocomplete-target="input"' in self.adresse_html

    def test_visible_input_targets_outer_carte_controller(self):
        # The outer wrapper mounts `carte-address-autocomplete`; the visible
        # input is also a target of that controller so it can populate the
        # input on geolocation success / reset on error.
        assert 'data-carte-address-autocomplete-target="input"' in self.adresse_html

    def test_show_on_focus_is_enabled(self):
        assert 'data-next-autocomplete-show-on-focus-value="true"' in self.adresse_html

    def test_endpoint_url_points_at_namespaced_view(self):
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

    def test_no_legacy_address_autocomplete_target_on_lat_lng(self):
        # Before the migration, lat/lng were targets of the legacy
        # address-autocomplete controller. They must point at the new one.
        assert "data-address-autocomplete-target" not in self.latitude_html
        assert "data-address-autocomplete-target" not in self.longitude_html
