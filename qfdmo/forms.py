from typing import List, cast

from django import forms
from django.core.cache import cache
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from dsfr.forms import DsfrBaseForm

from qfdmo.fields import GroupeActionChoiceField
from qfdmo.geo_api import epcis_from, formatted_epcis_as_list_of_tuple
from qfdmo.models import DagRun, DagRunStatus, SousCategorieObjet
from qfdmo.models.action import (
    Action,
    GroupeAction,
    get_action_instances,
    get_directions,
    get_ordered_directions,
)
from qfdmo.widgets import (
    AutoCompleteInput,
    DSFRCheckboxSelectMultiple,
    GenericAutoCompleteInput,
    RangeInput,
    SegmentedControlSelect,
)


class AddressesForm(forms.Form):
    def load_choices(self, request: HttpRequest, **kwargs) -> None:
        if address_placeholder := request.GET.get("address_placeholder"):
            self.fields["adresse"].widget.attrs["placeholder"] = address_placeholder

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
                "class": "fr-input fr-icon-search-line sm:qf-w-[596px]",
                "autocomplete": "off",
                "aria-label": "Indiquer un objet - obligatoire",
            },
            data_controller="ss-cat-object-autocomplete",
        ),
        help_text="pantalon, perceuse, canapé...",
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
                "class": "qf-w-full sm:qf-w-fit",
            },
            fieldset_attrs={
                "data-search-solution-form-target": "direction",
            },
        ),
        choices=[],
        # TODO: refacto forms : set initial value
        # initial="jai",
        label="Direction des actions",
        required=False,
    )

    pas_exclusivite_reparation = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "reparerFilter",
            }
        ),
        label=(
            "Masquer les adresses qui réparent uniquement les produits de leurs marques"
        ),
        help_text=(
            "Les adresses ne réparant que les produits de leur propre marque"
            " n'apparaîtront pas si cette case est cochée."
            " (uniquement valable lorsque l'action « réparer » est sélectionnée)"
        ),
        label_suffix="",
        required=False,
    )

    label_reparacteur = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "reparerFilter",
            }
        ),
        label="Adresses labellisées Répar’Acteurs",
        help_text=mark_safe(
            """Afficher uniquement les artisans labellisés
            (uniquement valable lorsque l'action « réparer » est sélectionnée).
            Les <span
                class="qf-underline qf-cursor-pointer
                qf-underline-offset-[3px] hover:qf-decoration-[1.5px]"
                title="Ouvre la modale Répar'Acteurs"
                onclick="document
                .getElementById('display_modale_reparacteur')
                .setAttribute('data-fr-opened', 'true');"
            >Répar'Acteurs</span>
             sont une initiative de la
            <a
                href='https://www.artisanat.fr/nous-connaitre/vous-accompagner/reparacteurs'
                target="_blank"
                rel="noreferrer"
                title="sur le site de la CMA - Nouvelle fenêtre"
            >
                Chambre des Métiers et de l’Artisanat
            </a>"""
        ),
        label_suffix="",
        required=False,
    )

    ess = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "fr-checkbox fr-m-1v"}),
        label="Adresses de l'économie sociale et solidaire",
        help_text=mark_safe(
            "Afficher uniquement les adresses recensées comme relevant de l'économie"
            " sociale et solidaire. En savoir plus sur le site <a href="
            '"https://www.economie.gouv.fr/cedef/economie-sociale-et-solidaire"'
            ' target="_blank" rel="noreferrer" title="economie.gouv.fr - Nouvelle'
            ' fenêtre">economie.gouv.fr</a>'
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
            "<span class='fr-icon--sm fr-icon-percent-line'></span>"
            "&nbsp;Adresses proposant le Bonus Réparation"
        ),
        help_text=mark_safe(
            "Afficher uniquement les adresses éligibles (uniquement valable lorsque l'"
            "action « réparer » est sélectionnée). En savoir plus sur le site <a href="
            '"https://www.ecologie.gouv.fr/bonus-reparation" target="_blank"'
            ' rel="noreferrer" title="Bonus réparation - Nouvelle fenêtre">Bonus'
            " réparation</a>"
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
                "class": "qf-w-full sm:qf-w-fit",
                "data-action": "click -> search-solution-form#advancedSubmit",
                "data-with-controls": "true",
            },
        ),
        choices=[
            (
                "0",
                mark_safe(
                    '<span class="fr-icon-road-map-line sm:qf-mx-1w">'
                    " à proximité</span>"
                ),
            ),
            (
                "1",
                mark_safe(
                    '<span class="fr-icon-global-line sm:qf-mx-1w"> en ligne</span>'
                ),
            ),
        ],
        label="Adresses à proximité ou solutions digitales",
        required=False,
    )


class FormulaireForm(AddressesForm):
    def load_choices(self, request: HttpRequest, **kwargs) -> None:
        # The kwargs in function signature prevents type error.
        # TODO : refacto forms : if AddressesForm and CarteAddressesForm
        # are used on differents views, the method signature would not need
        # to be the same.
        first_direction = request.GET.get("first_dir")
        self.fields["direction"].choices = [
            [direction["code"], direction["libelle"]]
            for direction in get_ordered_directions(first_direction=first_direction)
        ]
        super().load_choices(request)

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input sm:qf-w-[596px]",
                "autocomplete": "off",
                "aria-label": "Autour de l'adresse suivante - obligatoire",
            },
            data_controller="address-autocomplete",
        ),
        help_text="20 av. du Grésillé 49000 Angers",
        label="Autour de l'adresse suivante ",
        required=False,
    )


def get_epcis_for_carte_form():
    return [(code, code) for code in cast(List[str], epcis_from(["code"]))]


class CarteForm(AddressesForm):
    def load_choices(
        self,
        request: HttpRequest,
        grouped_action_choices: list[list[str]] = [],
        disable_reparer_option: bool = False,
    ) -> None:
        self.fields["grouped_action"].choices = [
            (
                self.fields["grouped_action"].label,
                grouped_action_choices,
            )
        ]
        self.fields["legend_grouped_action"].choices = [
            (
                self.fields["legend_grouped_action"].label,
                grouped_action_choices,
            )
        ]

        if disable_reparer_option:
            for field in ["bonus", "label_reparacteur", "pas_exclusivite_reparation"]:
                self.fields[field].widget.attrs["disabled"] = "true"

        super().load_choices(request)

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Rechercher autour d'une adresse",
                "autocomplete": "off",
                "aria-label": "Saisir une adresse - obligatoire",
            },
            data_controller="address-autocomplete",
        ),
        label="",
        required=False,
    )

    epci_codes = forms.MultipleChoiceField(
        choices=get_epcis_for_carte_form,
        widget=forms.MultipleHiddenInput(),
        required=False,
    )

    grouped_action = forms.MultipleChoiceField(
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": "fr-fieldset",
                "data-search-solution-form-target": "groupedActionInput",
                "data-action": (
                    "change -> search-solution-form#activeReparerFiltersCarte"
                ),
            },
        ),
        choices=[],
        label="Groupes d'actions",
        required=False,
    )

    # TODO : refacto forms, merge with grouped_action field
    legend_grouped_action = forms.MultipleChoiceField(
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": "fr-fieldset qf-mb-0",
                "data-action": (
                    "click -> search-solution-form#applyLegendGroupedAction"
                ),
            },
        ),
        choices=[],
        label="Groupes d'actions",
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


class ConfiguratorForm(DsfrBaseForm):
    # TODO: rename this field in all codebase -> actions_displayed
    action_list = GroupeActionChoiceField(
        queryset=GroupeAction.objects.all().order_by("order"),
        to_field_name="code",
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=GroupeAction.objects.exclude(code="trier"),
        label=mark_safe(
            "<h3>Informations disponibles sur la carte</h3>"
            "Choisissez les actions disponibles pour vos usagers."
        ),
        help_text="Ce sont les actions que vos usagers pourront consulter "
        "dans la carte que vous intègrerez. Par exemple, si vous ne voulez "
        "faire une carte que sur les points de collecte ou de réparation, il vous "
        "suffit de décocher toutes les autres actions possibles.",
    )
    epci_codes = forms.MultipleChoiceField(
        label=mark_safe(
            """
        <hr/>
        <h3>Paramètres de la carte</h3>
        1. Choisir les EPCI affichés par défaut sur la carte"""
        ),
        help_text="Commencez à taper un nom d’EPCI et sélectionnez un EPCI parmi "
        "les propositions de la liste.",
        # TODO: voir comment évaluer cela "lazily"
        # L'utilisation de lazy(all_epci_codes(...)) génère une erreur côté Django DSFR
        choices=formatted_epcis_as_list_of_tuple,
        widget=GenericAutoCompleteInput(
            attrs={"data-autocomplete-target": "hiddenInput", "class": "qf-hidden"},
            extra_attrs={
                "selected_label": "Vos EPCI sélectionnés",
                "empty_label": "Il n’y a pas d’EPCI sélectionné pour le moment",
                "endpoint": "/api/qfdmo/autocomplete/configurateur?query=",
                "additionnal_info": mark_safe(
                    render_to_string(
                        "forms/widgets/epci_codes_additionnal_info.html",
                    )
                ),
            },
        ),
    )

    limit = forms.IntegerField(
        widget=RangeInput(attrs={"max": 100, "min": 20}),
        initial=50,
        label="2. Nombre de résultats maximum à afficher sur la carte",
        help_text="Indiquez le nombre maximum de lieux qui pourront apparaître "
        "sur la carte suite à une recherche.",
        required=False,
    )


class AdvancedConfiguratorForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_choices()

    def load_choices(self):
        cached_directions = cast(
            List[dict], cache.get_or_set("directions", get_directions)
        )
        self.fields["direction"].choices = [
            (direction["code"], direction["libelle"]) for direction in cached_directions
        ] + [("no_dir", "Par défaut")]
        self.fields["first_dir"].choices = [
            ("first_" + direction["code"], direction["libelle"])
            for direction in cached_directions
        ] + [("first_no_dir", "Par défaut")]

        # Cast needed because of the cache
        cached_action_instances = cast(
            List[Action], cache.get_or_set("action_instances", get_action_instances)
        )
        self.fields["action_list"].choices = [
            (
                action.code,
                f"{action.libelle} ({action.libelle_groupe.capitalize()})",
            )
            for action in cached_action_instances
        ]
        self.fields["action_displayed"].choices = [
            (
                action.code,
                f"{action.libelle} ({action.libelle_groupe.capitalize()})",
            )
            for action in cached_action_instances
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
                "class": "qf-w-full sm:qf-w-fit",
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

    # - `data-direction`, option `jai` ou `jecherche`,
    # par défaut l'option de direction « Je cherche » est active
    direction = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qf-w-full sm:qf-w-fit",
            },
            fieldset_attrs={},
        ),
        # TODO: refacto forms : set initial value
        # initial="jecherche",
        label="Direction des actions",
        required=False,
    )

    # - `data-first_dir`, option `jai` ou `jecherche`, par défaut l'option de direction
    # « Je cherche » est affiché en premier dans la liste des options de direction
    first_dir = forms.ChoiceField(
        widget=SegmentedControlSelect(
            attrs={
                "class": "qf-w-full sm:qf-w-fit",
            },
            fieldset_attrs={},
        ),
        label="Direction affichée en premier dans la liste des options de direction",
        help_text="Cette option n'est disponible que dans la version formulaire",
        required=False,
    )

    action_displayed = forms.MultipleChoiceField(
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": (
                    "fr-checkbox qf-inline-grid qf-grid-cols-4 qf-gap-4" " qf-m-1w"
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
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": (
                    "fr-checkbox qf-inline-grid qf-grid-cols-4 qf-gap-4" " qf-m-1w"
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

    # - `data-max_width`, largeur maximum de l'iframe, la valeur par défaut est 100%
    max_width = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
            },
        ),
        label="Largeur maximum de l'iframe",
        help_text=mark_safe(
            "peut être exprimé en px, %, em, rem, vw, …<br>"
            "La valeur par défaut est 100%"
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
