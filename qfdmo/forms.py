from django import forms
from django.http import HttpRequest
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


class DSFRCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = "django/forms/widgets/checkbox_select.html"
    option_template_name = "django/forms/widgets/checkbox_option.html"


class AddressesForm(forms.Form):
    def load_choices(self, request: HttpRequest) -> None:
        pass

    bounding_box = forms.CharField(
        widget=forms.HiddenInput(
            attrs={
                "data-search-solution-form-target": "bbox",
                "data-map-target": "bbox",
            }
        ),
        required=False,
    )

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
        choices=[],
        label="Direction des actions",
        required=False,
    )

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
            },
        ),
        label=mark_safe(
            "<span class='fr-icon--sm fr-icon-money-euro-box-line'></span>"
            "&nbsp;Éligible au bonus réparation"
        ),
        help_text=mark_safe(
            "Afficher uniquement les adresses éligibles (uniquement valable lorsque le"
            " geste « réparer » est sélectionné). En savoir plus sur le site <a href="
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

    action_displayed = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    digital = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qfdmo-w-full md:qfdmo-w-fit",
                "data-action": "click -> search-solution-form#advancedSubmit",
                "data-with-controls": "true",
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


class IframeAddressesForm(AddressesForm):
    def load_choices(self, request: HttpRequest) -> None:
        first_direction = request.GET.get("first_dir")
        self.fields["direction"].choices = [
            [direction["code"], direction["libelle"]]
            for direction in CachedDirectionAction.get_directions(
                first_direction=first_direction
            )
        ]
        if address_placeholder := request.GET.get("address_placeholder"):
            self.fields["adresse"].widget.attrs["placeholder"] = address_placeholder

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


class CarteAddressesForm(AddressesForm):
    def load_choices(
        self,
        request: HttpRequest,
        groupe_options: list[list[str]] = [],
        disable_reparer_option: bool = False,
    ) -> None:
        self.fields["grouped_action"].choices = groupe_options
        if disable_reparer_option:
            self.fields["bonus"].widget.attrs["disabled"] = "true"
            self.fields["label_reparacteur"].widget.attrs["disabled"] = "true"
        if address_placeholder := request.GET.get("address_placeholder"):
            self.fields["adresse"].widget.attrs["placeholder"] = address_placeholder

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

    grouped_action = forms.MultipleChoiceField(
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": "fr-fieldset",
                "data-search-solution-form-target": "GroupeAction",
                "data-action": (
                    "change -> search-solution-form#activeReparerFiltersCarte"
                ),
            },
        ),
        choices=[],
        label="Actions",
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


class ConfiguratorForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_choices()

    def load_choices(self):
        self.fields["direction"].choices = [
            (direction["code"], direction["libelle"])
            for direction in CachedDirectionAction.get_directions()
        ]
        self.fields["first_dir"].choices = [
            ("first_" + direction["code"], direction["libelle"])
            for direction in CachedDirectionAction.get_directions()
        ]
        self.fields["action_list"].choices = [
            (
                action.code,
                f"{action.libelle} ({action.libelle_groupe.capitalize()})",
            )
            for action in CachedDirectionAction.get_action_instances()
        ]
        self.fields["action_displayed"].choices = [
            (
                action.code,
                f"{action.libelle} ({action.libelle_groupe.capitalize()})",
            )
            for action in CachedDirectionAction.get_action_instances()
        ]

    limit = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Nombre de résultats",
        help_text="Nombre de résultats affichés dans l'iframe",
        required=False,
    )

    address_placeholder = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Placeholder de l'adresse",
        help_text="Texte affiché dans le champ d'adresse",
        required=False,
    )

    iframe_mode = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qfdmo-w-full md:qfdmo-w-fit",
            },
            fieldset_attrs={
                "data-search-solution-form-target": "direction",
            },
        ),
        # FIXME: I guess async error comes from here
        choices=[
            ("carte", "Carte"),
            ("form", "Formulaire"),
        ],
        label="Mode de l'Iframe",
        required=False,
    )

    # - `data-direction`, option `jai` ou `jecherche`, par défaut l'option de direction « Je cherche » est active # noqa
    direction = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qfdmo-w-full md:qfdmo-w-fit",
            },
            fieldset_attrs={},
        ),
        label="Direction des actions",
        required=False,
    )

    # - `data-first_dir`, option `jai` ou `jecherche`, par défaut l'option de direction « Je cherche » est affiché en premier dans la liste des options de direction # noqa
    first_dir = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qfdmo-w-full md:qfdmo-w-fit",
            },
            fieldset_attrs={},
        ),
        label="Direction affichée en premier dans la liste des options de direction",
        help_text="Cette option n'est disponible que dans la version formulaire",
        required=False,
    )

    action_displayed = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": (
                    "fr-checkbox qfdmo-inline-grid qfdmo-grid-cols-4 qfdmo-gap-4"
                    " qfdmo-m-1w"
                ),
            },
        ),
        choices=[],
        label=mark_safe(
            "Liste des actions <strong>disponibles</strong> (selon la direction)"
        ),
        help_text=mark_safe(
            "Pour la direction « Je cherche » les actions possibles"
            " sont : « emprunter », « échanger », « louer », « acheter »<br>"
            "Pour la direction « J'ai » les actions possibles"
            " sont : « réparer », « prêter », « donner », « échanger », « mettre"
            " en location », « revendre »<br>"
            "Si le paramètre n'est pas renseigné ou est vide, toutes les actions"
            " éligibles à la direction sont disponibles"
        ),
        required=False,
    )

    # - `data-action_list`, liste des actions cochées selon la direction séparées par le caractère `|` : # noqa
    #   - pour la direction `jecherche` les actions possibles sont : `emprunter`, `echanger`, `louer`, `acheter` # noqa
    #   - pour la direction `jai` les actions possibles sont : `reparer`, `preter`, `donner`, `echanger`, `mettreenlocation`, `revendre` # noqa
    #   - si le paramètre `action_list` n'est pas renseigné ou est vide, toutes les actions éligibles à la direction sont cochées # noqa
    action_list = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": (
                    "fr-checkbox qfdmo-inline-grid qfdmo-grid-cols-4 qfdmo-gap-4"
                    " qfdmo-m-1w"
                ),
            },
        ),
        choices=[],
        label=mark_safe(
            "Liste des actions <strong>cochées</strong> (selon la direction)"
        ),
        help_text=mark_safe(
            "Pour la direction « Je cherche » les actions possibles"
            " sont : « emprunter », « échanger », « louer », « acheter »<br>"
            "Pour la direction « J'ai » les actions possibles"
            " sont : « réparer », « prêter », « donner », « échanger », « mettre"
            " en location », « revendre »<br>"
            "Si le paramètre n'est pas renseigné ou est vide, toutes les actions"
            " éligibles à la direction sont cochées"
        ),
        required=False,
    )

    # - `data-max_width`, largeur maximum de l'iframe, la valeur par défaut est 800px
    max_width = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Largeur maximum de l'iframe",
        help_text=mark_safe(
            "peut être exprimé en px, %, em, rem, vw, …<br>"
            "La valeur par défaut est 800px"
        ),
        required=False,
    )

    # - `data-height`, hauteur allouée à l'iframe cette hauteur doit être de 700px minimum, la valeur par défaut est 100vh # noqa
    height = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Hauteur de l'iframe",
        help_text=mark_safe(
            "peut être exprimé en px, %, em, rem, vh, …<br>"
            "La valeur par défaut est 100vh"
        ),
        required=False,
    )

    # - `data-iframe_attributes`, liste d'attributs au format JSON à ajouter à l'iframe
    iframe_attributes = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "fr-input", "rows": "3"},
        ),
        label="Attributs à appliquer à l'iframe",
        help_text=mark_safe("liste d'attributs au format JSON à ajouter à l'iframe"),
        required=False,
    )

    # TODO : documentation
    bounding_box = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Bounding box",
        help_text=mark_safe(
            "Bounding box au format JSON, ex: <br>"
            '{<br>&nbsp;&nbsp;"southWest":{"lat":48.916,"lng":2.298202514648438},'
            '<br>&nbsp;&nbsp;"northEast":{"lat":48.98742568330284,'
            '"lng":2.483596801757813}<br>}'
        ),
        required=False,
    )
