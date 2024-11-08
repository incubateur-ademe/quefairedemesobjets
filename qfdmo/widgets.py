from django import forms
from django.contrib.gis import forms as gis_forms
from django.forms import widgets


class RangeInput(widgets.NumberInput):
    template_name = "forms/widgets/range_input.html"
    input_type = "range"


class GenericAutoCompleteInput(widgets.Input):
    template_name = "forms/widgets/generic_autocomplete.html"
    hidden_template_name = widgets.MultipleHiddenInput.template_name

    def __init__(self, attrs=None, extra_attrs=None):
        super().__init__(attrs)
        self.extra_attrs = extra_attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["hidden_template_name"] = self.hidden_template_name
        context["extra_attrs"] = self.extra_attrs
        return context


class AutoCompleteInput(forms.TextInput):
    template_name = "forms/widgets/autocomplete.html"

    def __init__(self, attrs=None, data_controller="autocomplete", **kwargs):
        self.data_controller = data_controller
        super().__init__(attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["data_controller"] = self.data_controller
        return context


class SegmentedControlSelect(forms.RadioSelect):
    template_name = "forms/widgets/segmented_control.html"
    option_template_name = "forms/widgets/segmented_control_option.html"

    def __init__(self, attrs=None, fieldset_attrs=None, **kwargs):
        super().__init__(attrs, **kwargs)
        self.fieldset_attrs = {} if fieldset_attrs is None else fieldset_attrs.copy()

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["fieldset_attrs"] = self.fieldset_attrs
        # context["widget"]["fieldset_attrs"] = self.build_attrs(self.fieldset_attrs)
        return context


class DSFRCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = "forms/widgets/dsfr_checkbox_select.html"
    option_template_name = "forms/widgets/dsfr_checkbox_option.html"


class CustomOSMWidget(gis_forms.BaseGeometryWidget):
    # This widget is inspired from OSMWidget in django.contrib.gis.forms.widgets
    # but the SRID manipulation in geodjango breaks our implementation because the
    # raw coordinates displayed are in the wrong system, hence the partial rewrite
    # instead of inheritance.
    template_name = "admin/custom-openlayers-with-search.html"

    default_lon = 2.213749
    default_lat = 46.227638
    default_zoom = 5
    dataset_epsg = "EPSG:4326"
    map_epsg = "EPSG:3857"
    display_raw = True

    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/ol@v7.2.2/ol.css",
                "gis/css/ol3.css",
            )
        }
        js = (
            "https://cdn.jsdelivr.net/npm/ol@v7.2.2/dist/ol.js",
            "admin-map-widget.js",
        )

    def __init__(self, attrs=None):
        super().__init__(attrs)

        for key in (
            "dataset_epsg",
            "map_epsg",
            "default_zoom",
            "default_lat",
            "default_lon",
            "display_raw",
        ):
            self.attrs[key] = getattr(self, key)
        if attrs:
            self.attrs.update(attrs)

    def serialize(self, value):
        return value.json if value else ""
