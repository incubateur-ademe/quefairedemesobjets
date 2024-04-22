from django import forms
from django.utils.safestring import mark_safe

from qfdmo.models import CachedDirectionAction, DagRun, DagRunStatus, SousCategorieObjet


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


class IframeAddressesForm(forms.Form):
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
            [direction["code"], direction["libelle"]]
            for direction in CachedDirectionAction.get_directions(
                first_direction=first_direction
            )
        ]

    label_reparacteur = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "reparerFilter",
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

    ess = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "fr-checkbox fr-m-1v"}),
        label="Enseignes de l'économie sociale et solidaire",
        help_text=mark_safe(
            "Afficher uniquement les adresses recensées comme relevant de l'économie"
            " sociale et solidaire. En savoir plus sur le site <a href="
            '"https://www.economie.gouv.fr/cedef/economie-sociale-et-solidaire"'
            ' target="_blank" rel="noopener">economie.gouv.fr</a>'
        ),
        label_suffix="",
        required=False,
    )

    bonus = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "reparerFilter",
            }
        ),
        label=mark_safe(
            "<span class='fr-icon--sm fr-icon-money-euro-box-line'></span>"
            "&nbsp;Éligible au bonus réparation"
        ),
        help_text=mark_safe(
            "Afficher uniquement les adresses éligibles (uniquemet valable lorsque le"
            " geste « réparer » est sélectioné). En svoir plus sur le site <a href="
            '"https://www.ecologie.gouv.fr/bonus-reparation" target="_blank"'
            ' rel="noopener">Bonus réparation</a>'
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
                "data-action": "click -> search-solution-form#submitFormWithoutZone",
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


class CarteAddressesForm(IframeAddressesForm):
    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input md:qfdmo-max-w-[596px]",
                "placeholder": "20 av. du Grésillé 49000 Angers",
                "autocomplete": "off",
                "aria-label": "Saisir une adresse - obligatoire",
            },
            data_controller="address-autocomplete",
        ),
        label="Saisir une adresse ",
        required=False,
    )


class DagsForm(forms.Form):
    dagrun = forms.ModelChoiceField(
        label="Séléctionner l'execution d'un DAG",
        widget=forms.Select(
            attrs={
                "class": "fr-select",
            }
        ),
        queryset=DagRun.objects.filter(status=DagRunStatus.TO_VALIDATE.value),
        required=True,
    )
