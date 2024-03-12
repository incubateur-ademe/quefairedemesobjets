from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

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


class SegmentedControlSelect(forms.RadioSelect):
    template_name = "django/forms/widgets/segmented_control.html"
    option_template_name = "django/forms/widgets/segmented_control_option.html"

    def __init__(self, attrs=None, fieldset_attrs=None, option_attrs=None, choices=()):
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
                "class": "fr-input fr-icon-search-line md:qfdmo-w-[596px]",
                "placeholder": "chaussures, perceuse, canapé...",
                "autocomplete": "off",
                "aria-label": "Indiquer un objet - obligatoire",
            },
            data_controller="ss-cat-object-autocomplete",
        ),
        label="Indiquer un objet ",
        empty_label="",
        required=False,
    )
    sc_id = forms.IntegerField(
        widget=forms.HiddenInput(
            attrs={
                "data-ss-cat-object-autocomplete-target": "ssCat",
                "data-search-solution-form-target": "sousCategoryObjetID",
            }
        ),
        required=False,
    )

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input md:qfdmo-w-[596px]",
                "placeholder": "20 av. du Grésillé 49000 Angers",
                "autocomplete": "off",
                "aria-label": "Autour de l'adresse suivante - obligatoire",
            },
            data_controller="address-autocomplete",
        ),
        label="Autour de l'adresse suivante ",
        required=False,
    )
    latitude = forms.FloatField(
        widget=forms.HiddenInput(
            attrs={
                "data-address-autocomplete-target": "latitude",
                "data-search-solution-form-target": "latitudeInput",
            }
        ),
        required=False,
    )
    longitude = forms.FloatField(
        widget=forms.HiddenInput(
            attrs={
                "data-address-autocomplete-target": "longitude",
                "data-search-solution-form-target": "longitudeInput",
            }
        ),
        required=False,
    )

    direction = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "data-action": "click -> search-solution-form#changeDirection",
                "class": "qfdmo-w-full md:qfdmo-w-fit",
            },
            fieldset_attrs={
                "data-search-solution-form-target": "direction",
            },
        ),
        # FIXME: I guess async error comes from here
        choices=[],
        label="Direction des actions",
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
            }
        ),
        label="Label Répar’Acteurs",
        help_text=mark_safe(
            "Afficher uniquement les artisans labellisés (uniquement valable lorsque le"
            " geste « réparer » est sélectionné). En savoir plus <a href="
            '"https://www.artisanat.fr/nous-connaitre/vous-accompagner/reparacteurs"'
            ' target="_blank" rel="noopener"> sur le site de la CMA</a>'
        ),
        label_suffix="",
        required=False,
    )

    action_list = forms.CharField(
        widget=forms.HiddenInput(
            attrs={"data-search-solution-form-target": "actionList"},
        ),
        required=False,
    )

    digital = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qfdmo-w-full md:qfdmo-w-fit",
                "data-action": "click -> search-solution-form#submitForm",
            },
        ),
        choices=[
            (
                "0",
                mark_safe(
                    '<span class="fr-icon-road-map-line md:qfdmo-mx-1w">'
                    " à proximité</span>"
                ),
            ),
            (
                "1",
                mark_safe(
                    '<span class="fr-icon-global-line md:qfdmo-mx-1w"> en ligne</span>'
                ),
            ),
        ],
        label="Adresses à proximité ou solutions digitales",
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
