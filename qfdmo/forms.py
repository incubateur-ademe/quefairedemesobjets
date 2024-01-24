from django import forms
from django.conf import settings

from qfdmo.models import (
    CachedDirectionAction,
    CorrectionActeurStatus,
    SousCategorieObjet,
)


class AutoCompleteInput(forms.Select):
    template_name = "django/forms/widgets/autocomplete.html"

    def __init__(self, attrs=None, data_controller="autocomplete", **kwargs):
        self.data_controller = data_controller
        super().__init__(attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["data_controller"] = self.data_controller
        return context


class InlineRadioSelect(forms.RadioSelect):
    template_name = "django/forms/widgets/inline_radio.html"
    option_template_name = "django/forms/widgets/inline_radio_option.html"

    def __init__(self, attrs=None, fieldset_attrs=None, choices=()):
        self.fieldset_attrs = {} if fieldset_attrs is None else fieldset_attrs.copy()
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["fieldset_attrs"] = self.build_attrs(self.fieldset_attrs)
        return context


class GetReemploiSolutionForm(forms.Form):
    sous_categorie_objet = forms.ModelChoiceField(
        queryset=SousCategorieObjet.objects.all(),
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input fr-icon-search-line",
                "placeholder": "vêtement, smartphone, meuble...",
                "autocomplete": "off",
            },
            data_controller="ss-cat-object-autocomplete",
        ),
        label="",
        empty_label="",
        required=False,
    )
    sc_id = forms.IntegerField(
        widget=forms.HiddenInput(
            attrs={"data-ss-cat-object-autocomplete-target": "ssCat"}
        ),
        required=False,
    )

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "20 av. du Grésillé 49000 Angers",
                "autocomplete": "off",
            },
            data_controller="address-autocomplete",
        ),
        label="Autour de l'adresse suivante ",
        required=False,
    )
    latitude = forms.FloatField(
        widget=forms.HiddenInput(
            attrs={"data-address-autocomplete-target": "latitude"}
        ),
        required=False,
    )
    longitude = forms.FloatField(
        widget=forms.HiddenInput(
            attrs={"data-address-autocomplete-target": "longitude"}
        ),
        required=False,
    )

    direction = forms.ChoiceField(
        widget=InlineRadioSelect(
            attrs={
                "class": "fr-radio",
                "data-action": "click -> search-solution-form#changeDirection",
            },
            fieldset_attrs={
                "class": "fr-fieldset fr-my-1w",
                "data-search-solution-form-target": "direction",
            },
        ),
        # FIXME: I guess async error comes from here
        choices=[],
        label="",
        required=False,
    )

    def load_choices(self, first_direction=None):
        self.fields["direction"].choices = [
            [direction["nom"], direction["nom_affiche"]]
            for direction in CachedDirectionAction.get_directions(
                first_direction=first_direction
            )
        ]

    label_reparacteur = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "advancedFiltersField",
                "data-action": "click -> search-solution-form#updateAdvancedFiltersCounter",  # noqa E501
            }
        ),
        label="Label Répar’Acteurs",
        help_text="Afficher uniquement les artisans labellisés",
        label_suffix="",
        required=False,
    )

    action_list = forms.CharField(
        widget=forms.HiddenInput(
            attrs={"data-search-solution-form-target": "actionList"},
        ),
        required=False,
    )

    digital = forms.BooleanField(
        widget=forms.HiddenInput(
            attrs={"data-search-solution-form-target": "digital"},
        ),
        required=False,
    )


class GetCorrectionsForm(forms.Form):
    source = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )
    correction_statut = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        choices=CorrectionActeurStatus.choices,
        label="Statut de la correction",
        required=False,
    )
    nb_lines = forms.IntegerField(
        initial=settings.NB_CORRECTION_DISPLAYED,
        widget=forms.NumberInput(
            attrs={
                "class": "fr-input",
            }
        ),
        label="Nombre de corrections à afficher",
        min_value=1,
        max_value=100,
    )
    search_query = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Nom, Ville, Code postal, Siret…",
            }
        ),
        label="Recherche textuelle",
        required=False,
    )
