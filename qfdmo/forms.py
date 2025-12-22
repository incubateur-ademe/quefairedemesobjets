import base64
import json
import uuid
from typing import cast

from django import forms
from django.core.cache import cache
from django.db.models import TextChoices
from django.db.utils import cached_property
from django.http import HttpRequest, QueryDict
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from dsfr.enums import SegmentedControlChoices
from dsfr.forms import DsfrBaseForm
from dsfr.widgets import SegmentedControl

from qfdmd.models import Synonyme
from qfdmo.fields import GroupeActionChoiceField, LabelQualiteChoiceField
from qfdmo.geo_api import formatted_epcis_as_list_of_tuple
from qfdmo.mixins import AutoSubmitMixin, CarteConfigFormMixin, GetFormMixin
from qfdmo.models import SousCategorieObjet
from qfdmo.models.acteur import LabelQualite
from qfdmo.models.action import (
    Action,
    GroupeAction,
    get_action_instances,
    get_directions,
)
from qfdmo.models.config import CarteConfig
from qfdmo.widgets import (
    AutoCompleteInput,
    DSFRCheckboxSelectMultiple,
    GenericAutoCompleteInput,
    RangeInput,
    SegmentedControlSelect,
)


class MapForm(GetFormMixin, CarteConfigFormMixin, forms.Form):
    """
    Form that manages geographic search parameters for the map interface.

    This form contains both visible and hidden fields used to filter and display
    Acteur results on the map:

    - `adresse`: Visible autocomplete input field where users type an address
    - `bounding_box`, `latitude`, `longitude`: Hidden fields automatically populated
      by the MapLibre controller based on map interactions (panning, zooming,
      address selection)

    The hidden fields are not directly controlled by the user but are managed by
    the address-autocomplete and maplibre Stimulus controllers in the frontend.

    ⚠️⚠️⚠️ If this form must evolve, especially the attributes set on the fields,
    the changes must be backported to qfdmo.forms.FormulaireForm.
    """

    carte_config_initial_mapping = {
        "bounding_box": "bounding_box",
    }

    def _override_field_initial_from_carte_config(self) -> None:
        """Override parent to handle bounding_box conversion from
        PolygonField to JSON string."""
        super()._override_field_initial_from_carte_config()

        # Handle bounding_box conversion from PolygonField to JSON string
        if self.carte_config and self.carte_config.bounding_box:
            polygon = self.carte_config.bounding_box
            # Extract coordinates: polygon.extent gives (xmin, ymin, xmax, ymax)
            # which is (west, south, east, north)
            extent = polygon.extent
            bounding_box_json = {
                "southWest": {"lat": extent[1], "lng": extent[0]},
                "northEast": {"lat": extent[3], "lng": extent[2]},
            }
            self.fields["bounding_box"].initial = json.dumps(bounding_box_json)

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Rechercher autour d'une adresse",
                "autocomplete": "off",
                "aria-label": "Saisir une adresse - obligatoire",
                "data-testid": "carte-adresse-input",
            },
            data_controller="address-autocomplete",
        ),
        label="",
        required=False,
    )
    bounding_box = forms.CharField(
        widget=forms.HiddenInput(
            attrs={
                "data-search-solution-form-target": "bbox",
                "data-map-target": "bbox",
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

    def _apply_legacy_querystring_overrides(self, legacy_form):
        if not legacy_form:
            return

        request_data = legacy_form.decode_querystring()

        # Handle action_displayed: filter the queryset
        if bounding_box := request_data.get("bounding_box"):
            self.fields["bounding_box"].initial = bounding_box


class FormulaireForm(forms.Form):
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

    sous_categorie_objet = forms.ModelChoiceField(
        queryset=SousCategorieObjet.objects.all(),
        to_field_name="libelle",
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

    pas_exclusivite_reparation = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-checkbox fr-m-1v",
                "data-search-solution-form-target": "reparerFilter",
            }
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
        label=render_to_string(
            "ui/components/formulaire/filtres/reparacteurs/label.html"
        ),
        label_suffix="",
        required=False,
    )

    ess = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "fr-checkbox fr-m-1v"}),
        label=render_to_string("ui/components/formulaire/filtres/ess/label.html"),
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
        label=render_to_string("ui/components/formulaire/filtres/bonus/label.html"),
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

    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input sm:qf-w-[596px]",
                "autocomplete": "off",
                "aria-label": "Autour de l'adresse suivante - obligatoire",
                "data-testid": "formulaire-adresse-input",
            },
            data_controller="address-autocomplete",
        ),
        help_text="20 av. du Grésillé 49000 Angers",
        label="Autour de l'adresse suivante ",
        required=False,
    )


class LegendeForm(GetFormMixin, CarteConfigFormMixin, DsfrBaseForm):
    carte_config_choices_mapping = {
        "groupe_action": "groupe_action",
    }
    carte_config_initial_mapping = {
        "groupe_action": "groupe_action",
    }

    groupe_action = GroupeActionChoiceField(
        queryset=GroupeAction.objects.filter(afficher=True)
        .prefetch_related("actions")
        .order_by("order"),
        to_field_name="id",
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="",
        initial=GroupeAction.objects.filter(afficher=True).prefetch_related("actions"),
    )

    def _apply_legacy_querystring_overrides(self, legacy_form):
        """Apply legacy querystring parameters to override form behavior.

        - action_displayed: filters the queryset for groupe_action field
        - action_list: sets the initial value for groupe_action field

        Querystring parameters override carte_config if present.
        """
        if not legacy_form:
            return

        request_data = legacy_form.decode_querystring()

        # Handle action_displayed: filter the queryset
        if action_displayed := request_data.get("action_displayed"):
            # Split pipe-separated action codes
            action_codes = [
                code.strip() for code in action_displayed.split("|") if code.strip()
            ]

            if action_codes:
                # Filter groupe_action based on actions with these codes
                groupe_action_qs = (
                    GroupeAction.objects.filter(
                        actions__code__in=action_codes, afficher=True
                    )
                    .prefetch_related("actions")
                    .distinct()
                    .order_by("order")
                )

                # Override the queryset
                self.fields["groupe_action"].queryset = groupe_action_qs

        # Handle action_list: set initial value
        if action_list := request_data.get("action_list"):
            # Split pipe-separated action codes
            action_codes = [
                code.strip() for code in action_list.split("|") if code.strip()
            ]

            if action_codes:
                # Get GroupeAction instances that contain these actions
                initial_groupe_actions = (
                    GroupeAction.objects.filter(
                        actions__code__in=action_codes, afficher=True
                    )
                    .prefetch_related("actions")
                    .distinct()
                    .order_by("order")
                )

                # Set as initial value
                self.fields["groupe_action"].initial = initial_groupe_actions

    @cached_property
    def visible(self):
        return self.fields["groupe_action"].queryset.count() > 1


class LegacySupportForm(GetFormMixin, forms.Form):
    querystring = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
    )

    query_params_to_keep = [
        "action_list",
        "action_displayed",
        "label_reparacteur",
        "pas_exclusivite_reparation",
        "epci_codes",
        "bounding_box",
        "sc_id",
    ]

    def __init__(self, *args, **kwargs):
        # Extract request from kwargs to get the initial querystring
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # On first load (GET request with no form data), capture the querystring
        if request and request.method == "GET":
            # Filter query params to only keep those in query_params_to_keep
            filtered_query_dict = request.GET.copy()

            # Remove params that are not in query_params_to_keep
            for key in list(filtered_query_dict.keys()):
                if key not in self.query_params_to_keep:
                    del filtered_query_dict[key]

            # Build the filtered querystring and encode as base64
            if filtered_query_dict:
                filtered_querystring = filtered_query_dict.urlencode()
                encoded_querystring = base64.b64encode(
                    filtered_querystring.encode("utf-8")
                ).decode("utf-8")
                self.fields["querystring"].initial = encoded_querystring

    def decode_querystring(self) -> QueryDict:
        """Decode a base64-encoded querystring and parse it into a QueryDict"""
        encoded_querystring = self["querystring"].value()
        if not encoded_querystring:
            return QueryDict()

        try:
            decoded_bytes = base64.b64decode(encoded_querystring)
            decoded_querystring = decoded_bytes.decode("utf-8")
            return QueryDict(decoded_querystring)
        except (ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode querystring: {e}") from e


class AutoSubmitLegendeForm(AutoSubmitMixin, LegendeForm):
    autosubmit_fields = ["groupe_action"]


class NextAutocompleteInput(forms.TextInput):
    template_name = "ui/forms/widgets/autocomplete/input.html"

    def __init__(
        self,
        search_view,
        limit=5,
        *args,
        **kwargs,
    ):
        # TODO: add optional template args
        self.search_view = search_view
        self.limit = limit
        self.turbo_frame_id = str(uuid.uuid4())

        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        endpoint_url = reverse(self.search_view)
        return {
            **context,
            "endpoint_url": endpoint_url,
            "limit": self.limit,
            "turbo_frame_id": self.turbo_frame_id,
        }


class FiltresForm(GetFormMixin, CarteConfigFormMixin, DsfrBaseForm):
    carte_config_initial_mapping = {
        "label_qualite": "label_qualite",
        "bonus": "bonus_reparation",
    }
    synonyme = forms.ModelChoiceField(
        queryset=Synonyme.objects.all(),
        widget=NextAutocompleteInput(
            search_view="autocomplete_synonyme",
        ),
        help_text="pantalon, perceuse, canapé...",
        label="Indiquer un objet",
        required=False,
    )

    bonus = forms.BooleanField(
        required=False,
        initial=False,
        label=render_to_string("ui/components/label_qualite/filtre_bonus.html"),
        help_text="Uniquement les acteurs proposant le Bonus Réparation (Disponible"
        ' pour l\'action "Je répare")',
    )

    label_qualite = LabelQualiteChoiceField(
        queryset=LabelQualite.objects.filter(afficher=True, filtre=True),
        to_field_name="code",
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="",
    )

    pas_exclusivite_reparation = forms.BooleanField(
        required=False,
        initial=True,
        label="Masquer les lieux qui réparent uniquement les produits de leurs marques",
        help_text="Les adresses ne réparant que les produits de leur propre marque "
        "n'apparaîtront pas si cette case est cochée. (uniquement valable lorsque"
        " l'action « réparer » est sélectionnée)",
    )

    def _apply_legacy_querystring_overrides(self, legacy_form):
        """Apply legacy querystring parameters to override form behavior.

        - label_reparacteur: set initial value to reparacteur checked
        """
        if not legacy_form:
            return

        initial_legacy_request_data = legacy_form.decode_querystring()

        if label_reparacteur := initial_legacy_request_data.get("label_reparacteur"):
            if label_reparacteur == "true":
                # Set as initial value
                self.fields["label_qualite"].initial = LabelQualite.objects.filter(
                    code="reparacteur"
                )

        if pas_exclusivite_reparation := initial_legacy_request_data.get(
            "pas_exclusivite_reparation"
        ):
            self.fields["pas_exclusivite_reparation"].initial = (
                pas_exclusivite_reparation == "false"
            )


class FiltresFormWithoutSynonyme(FiltresForm):
    # Explicitly remove the synonyme field by setting it to None
    synonyme = None


class DigitalActeurForm(GetFormMixin, DsfrBaseForm):
    class DigitalChoices(TextChoices, SegmentedControlChoices):
        DIGITAL = {
            "value": "digital",
            "label": "En ligne",
            "icon": "global-line",
        }
        PHYSIQUE = {
            "value": "physique",
            "label": "À proximité",
            "icon": "road-map-line",
        }

    digital = forms.ChoiceField(
        # TODO : gérer pour l'accessibilité
        label="",
        choices=DigitalChoices.choices,
        initial=DigitalChoices.PHYSIQUE.value,
        required=False,
        widget=SegmentedControl(
            extended_choices=DigitalChoices,
            attrs={
                "data-action": "search-solution-form#advancedSubmit",
            },
        ),
    )


class ActionDirectionForm(GetFormMixin, DsfrBaseForm):
    class DirectionChoices(TextChoices, SegmentedControlChoices):
        J_AI = {
            "value": "jai",
            "label": "J'ai un objet",
        }
        JE_CHERCHE = {
            "value": "jecherche",
            "label": "Je recherche un objet",
        }

    direction = forms.ChoiceField(
        widget=SegmentedControl(
            attrs={
                "data-action": "click -> search-solution-form#changeDirection",
                "data-search-solution-form-target": "direction",
                "class": "qf-w-full sm:qf-w-fit",
            },
            extended_choices=DirectionChoices,
        ),
        choices=DirectionChoices.choices,
        # TODO: handle label in UI without displaying it
        label="",
        # label="Direction des actions",
        required=False,
    )


class ConfiguratorForm(DsfrBaseForm):
    # TODO: rename this field in all codebase -> actions_displayed
    action_list = GroupeActionChoiceField(
        queryset=GroupeAction.objects.all()
        .prefetch_related("actions")
        .order_by("order"),
        to_field_name="code",
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=GroupeAction.objects.exclude(code="trier").prefetch_related("actions"),
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
                        "ui/forms/widgets/epci_codes_additionnal_info.html",
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
            list[dict], cache.get_or_set("directions", get_directions)
        )
        self.fields["direction"].choices = [
            (direction["code"], direction["libelle"]) for direction in cached_directions
        ] + [("no_dir", "Par défaut")]

        # Cast needed because of the cache
        cached_action_instances = cast(
            list[Action], cache.get_or_set("action_instances", get_action_instances)
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

    action_displayed = forms.MultipleChoiceField(
        widget=DSFRCheckboxSelectMultiple(
            attrs={
                "class": ("fr-checkbox qf-inline-grid qf-grid-cols-4 qf-gap-4 qf-m-1w"),
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
                "class": ("fr-checkbox qf-inline-grid qf-grid-cols-4 qf-gap-4 qf-m-1w"),
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


class GroupeActionForm(GetFormMixin, DsfrBaseForm):
    pass


class ViewModeForm(AutoSubmitMixin, GetFormMixin, CarteConfigFormMixin, DsfrBaseForm):
    carte_config_initial_mapping = {
        "view": "mode_affichage",
    }

    autosubmit_fields = ["view"]

    class ViewModeSegmentedControlChoices(TextChoices, SegmentedControlChoices):
        CARTE = {
            "value": CarteConfig.ModesAffichage.CARTE.value,
            "label": CarteConfig.ModesAffichage.CARTE.label,
            "icon": "map-pin-2-fill",
        }
        LISTE = {
            "value": CarteConfig.ModesAffichage.LISTE.value,
            "label": CarteConfig.ModesAffichage.LISTE.label,
            "icon": "list-unordered",
        }

    view = forms.ChoiceField(
        label="",
        choices=ViewModeSegmentedControlChoices.choices,
        required=False,
        initial=CarteConfig.ModesAffichage.CARTE,
        widget=SegmentedControl(
            extra_classes="max-nolegend:fr-segmented--sm",
            extended_choices=ViewModeSegmentedControlChoices,
        ),
    )
