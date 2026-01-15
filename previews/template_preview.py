# Ignore line length recommandations from flake8
# flake8: noqa: E501
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.paginator import Paginator
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory
from django_lookbook.preview import LookbookPreview
from django_lookbook.utils import register_form_class
from dsfr.forms import DsfrBaseForm

from core.constants import DEFAULT_MAP_CONTAINER_ID
from core.widgets import (
    HomeSearchAutocompleteInput,
    SynonymeAutocompleteInput,
)
from infotri.forms import InfotriForm
from qfdmd.forms import SearchForm
from qfdmd.models import Synonyme
from qfdmo.forms import (
    LegendeForm,
    ViewModeForm,
)
from qfdmo.models.acteur import (
    ActeurType,
    DisplayedActeur,
    DisplayedPropositionService,
    LabelQualite,
)
from qfdmo.models.action import Action
from qfdmo.models.config import CarteConfig

base_url = settings.BASE_URL


def component_docs(md_file_path):
    """
    Decorator that automatically loads and injects markdown documentation
    from a .md file into the preview method's docstring.

    Usage:
        @component_docs("ui/components/button.md")
        def button(self, **kwargs):
            context = {"href": "google.fr", "text": "test"}
            return render_to_string("ui/components/button.html", context)

    The decorator will look for templates/ui/components/button.md and inject
    its content as the method's docstring for django-lookbook to display.
    """

    def decorator(func):
        # Load the markdown documentation
        base_dir = Path(settings.BASE_DIR)
        templates_dir = base_dir / "templates"
        md_path = templates_dir / md_file_path

        if md_path.exists():
            func.__doc__ = md_path.read_text()

        return func

    return decorator


class ProduitHeadingForm(forms.Form):
    """
    Form for produit heading with synonyme and pronom choices
    """

    synonyme = forms.CharField(
        label="Synonyme",
        max_length=100,
        help_text="Entrez le nom d'un synonyme",
        initial="",
        required=False,
    )

    pronom = forms.ChoiceField(
        label="Pronom",
        choices=[
            ("mon", "mon"),
            ("ma", "ma"),
            ("mes", "mes"),
        ],
        help_text="Choisissez le pronom",
        initial="mon",
    )


class CarteConfigForm(forms.Form):
    """
    Form for carte config
    """

    def get_first_carte_config():
        return CarteConfig.objects.first()

    carte_config = forms.ModelChoiceField(
        label="Carte config",
        help_text="Carte config",
        required=False,
        queryset=CarteConfig.objects.all(),
        initial=get_first_carte_config,
    )


def get_default_action():
    return Action.objects.get(code="reparer")


class PinPointForm(forms.Form):
    action = forms.ModelChoiceField(
        queryset=Action.objects.all(),
        label="Action",
        to_field_name="code",
        help_text="Sélectionnez une action",
        initial=get_default_action,
    )
    avec_bonus = forms.BooleanField(
        label="Avec bonus",
        help_text="Avec bonus",
        initial=False,
    )
    carte = forms.BooleanField(
        label="Carte",
        help_text="Carte",
        initial=True,
    )
    carte_config = forms.ModelChoiceField(
        label="Carte config",
        help_text="Carte config",
        required=False,
        queryset=CarteConfig.objects.all(),
    )
    acteur_type = forms.ModelChoiceField(
        label="Acteur type",
        help_text="Action list",
        to_field_name="code",
        required=False,
        queryset=ActeurType.objects.all(),
        initial="",
    )


class CartePreview(LookbookPreview):
    """
    Previews for carte components
    """

    @component_docs("ui/components/carte/mode_liste.md")
    def mode_liste(self, **kwargs):
        acteurs = DisplayedActeur.objects.all()[:10]
        paginator = Paginator(acteurs, 5)
        page = paginator.get_page(1)

        # Create a fake request for the context
        factory = RequestFactory()
        request = factory.get("/")

        context = {
            "paginated_acteurs_obj": page,
            "count": acteurs.count(),
            "CARTE": {"ajouter_un_lieu_mode_liste": "Proposer une adresse"},
            "map_container_id": DEFAULT_MAP_CONTAINER_ID,
            "forms": {
                "legende": LegendeForm(),
                "filtres_form": None,
            },
            "request": request,
        }
        return render_to_string("ui/components/carte/mode_liste.html", context)

    @component_docs("ui/components/carte/legend.md")
    def legend(self, **kwargs):
        context = {
            "forms": {
                "legende": LegendeForm(),
                "filtres_form": None,
            },
            "carte_config": None,
        }
        return render_to_string("ui/components/carte/legend.html", context)

    @component_docs("ui/components/carte/buttons/ajouter_un_lieu.md")
    def ajouter_un_lieu(self, **kwargs):
        context = {"CARTE": {"ajouter_un_lieu": "Proposer une adresse"}}
        return render_to_string(
            "ui/components/carte/buttons/ajouter_un_lieu.html", context
        )

    @component_docs("ui/components/carte/buttons/ajouter_un_lieu_mode_liste.md")
    def ajouter_un_lieu_mode_liste(self, **kwargs):
        context = {"CARTE": {"ajouter_un_lieu_mode_liste": "Proposer une adresse"}}
        return render_to_string(
            "ui/components/carte/buttons/ajouter_un_lieu_mode_liste.html", context
        )


class ComponentsPreview(LookbookPreview):
    @register_form_class(PinPointForm)
    @component_docs("templatetags/acteur_pinpoint.md")
    def acteur_pinpoint(
        self,
        action="reparer",
        avec_bonus="False",
        carte="True",
        carte_config=None,
        acteur_type=None,
        **kwargs,
    ):
        try:
            # FIXME : avec_bonus is returned as a string by the lookbook where I expected
            # a boolean
            # We suspect an issue upstream in django-lookbook, this might need to be investigated
            # and raised to the maintainer.
            if isinstance(action, str) and action:
                action = Action.objects.get(code=action)
            if isinstance(carte_config, str) and carte_config:
                carte_config = CarteConfig.objects.get(id=carte_config)
            if isinstance(acteur_type, str) and acteur_type:
                acteur_type = ActeurType.objects.get(code=acteur_type)
            if isinstance(avec_bonus, str):
                avec_bonus = avec_bonus.lower() == "true"
            if isinstance(carte, str):
                carte = carte.lower() == "true"

            displayed_proposition_service = DisplayedPropositionService.objects.filter(
                action=action
            )
            if acteur_type:
                displayed_proposition_service = displayed_proposition_service.filter(
                    acteur__acteur_type=acteur_type
                )
            if avec_bonus:
                displayed_proposition_service = displayed_proposition_service.filter(
                    acteur__labels__bonus=True
                )
            else:
                displayed_proposition_service = displayed_proposition_service.exclude(
                    acteur__in=DisplayedActeur.objects.filter(labels__bonus=True)
                )
            displayed_proposition_service = displayed_proposition_service.first()
            if not displayed_proposition_service:
                raise ValueError(f"PropositionService with action `{action}` not found")
        except Exception as e:
            template = Template(
                "Une erreur s'est produite dans la génération de la preview,"
                f" la combinaison de filtres ne permet pas d'afficher un pinpoint <br><pre>{e}</pre>",
            )

            return template.render(Context({}))

        context = {
            "acteur": displayed_proposition_service.acteur,
            "direction": action.directions.first().code,
            "action_list": action.code,
            "carte": carte,
            "carte_config": carte_config,
            "sc_id": displayed_proposition_service.sous_categories.first().id,
        }
        template = Template(
            """
            {% load carte_tags %}
            {% acteur_pinpoint_tag acteur=acteur direction=direction action_list=action_list carte=carte carte_config=carte_config sous_categorie_id=sc_id force_visible=True %}
            """
        )
        return template.render(Context(context))

    def acteur_pinpoint_multiple(self, **kwargs):
        """
        Preview showing two pinpoints side by side to test active state toggling.
        Uses dummy acteur objects to avoid generating real links.
        """

        class DummyActeur:
            def __init__(self, latitude, longitude, uuid, *args, **kwargs):
                self.latitude = latitude
                self.longitude = longitude
                self.uuid = uuid
                self.location = Point(longitude, latitude)
                self.action_to_display = lambda *args, **kwargs: None
                self.full_url = "#"

        acteur_1 = DummyActeur(48.8566, 2.3522, "dummy-1")
        acteur_2 = DummyActeur(48.8606, 2.3376, "dummy-2")

        context = {
            "acteur_1": acteur_1,
            "acteur_2": acteur_2,
        }
        template = Template(
            """
            {% load carte_tags %}
            <div class="qf-flex qf-gap-4 qf-p-4" data-controller="map">
                <div data-testid="pinpoint-1">
                    {% acteur_pinpoint_tag acteur=acteur_1 %}
                </div>
                <div data-testid="pinpoint-2">
                    {% acteur_pinpoint_tag acteur=acteur_2 %}
                </div>
            </div>
            """
        )
        return template.render(Context(context))

    @component_docs("ui/components/button.md")
    def button(self, **kwargs):
        context = {"href": "google.fr", "text": "test"}
        return render_to_string("ui/components/button.html", context)

    @component_docs("ui/components/code/code.md")
    def code(self, **kwargs):
        context = {
            "script": '<script src="https://quefairedemesdechets.ademe.local/iframe.js"></script>',
        }
        return render_to_string("ui/components/code/code.html", context)

    @component_docs("ui/components/logo/header.md")
    def logo(self, **kwargs):
        return render_to_string("ui/components/logo/header.html")

    @component_docs("ui/components/logo/homepage.md")
    def logo_homepage(self, **kwargs):
        return render_to_string("ui/components/logo/homepage.html")

    @component_docs("ui/components/produit/legacy_heading.md")
    def produit_legacy_heading(self, **kwargs):
        context = {"title": "Coucou !"}
        return render_to_string("ui/components/produit/legacy_heading.html", context)

    @register_form_class(ProduitHeadingForm)
    @component_docs("ui/components/produit/heading.md")
    def produit_heading(self, synonyme=None, pronom="mon", **kwargs):
        context = {"title": "Coucou !"}

        if synonyme:
            context.update(synonyme=synonyme)

        context.update(pronom=pronom)

        return render_to_string("ui/components/produit/heading.html", context)

    @register_form_class(ProduitHeadingForm)
    @component_docs("ui/components/produit/heading_family.md")
    def produit_heading_family(self, synonyme=None, pronom="mon", **kwargs):
        context = {"label": "youpi", "title": "Coucou !"}

        if synonyme:
            context.update(synonyme=synonyme)

        context.update(pronom=pronom)

        return render_to_string("ui/components/produit/heading_family.html", context)

    @component_docs("ui/components/mini_carte/mini_carte.md")
    def mini_carte(self, **kwargs):
        context = {"preview": True, "acteur": None, "home": None}
        context.update(acteur=DisplayedActeur.objects.first(), location=Point(-2, 48))

        return render_to_string("ui/components/mini_carte/mini_carte.html", context)

    @component_docs("ui/components/spinner.md")
    def spinner(self, **kwargs):
        context = {"small": False}
        return render_to_string("ui/components/spinner.html", context)

    @component_docs("ui/components/spinner.md")
    def spinner_small(self, **kwargs):
        context = {"small": True}
        return render_to_string("ui/components/spinner.html", context)

    def label_qualite_dsfr_tag(self, **kwargs):
        context = {"label": LabelQualite.objects.get(code="bonusrepar")}
        return render_to_string("ui/components/label_qualite/dsfr_label.html", context)

    def label_qualite(self, **kwargs):
        template = Template(
            """
            {% load acteur_tags %}
            {% acteur_label %}
            """
        )
        context = {
            "object": DisplayedActeur.objects.filter(
                labels__code__in=["bonusrepar"],
            ).first()
        }
        return template.render(Context(context))

    def service_tag(self, **kwargs):
        """Preview for service tags in both default and formulaire modes"""
        action = Action.objects.first()
        if not action:
            return "No actions available in database"

        context_default = {
            "action": action,
            # is_formulaire not set, defaults to False
        }
        context_formulaire = {
            "action": action,
            "is_formulaire": True,
        }

        # Render both versions to show the difference
        default_html = Template(
            """
            {% load acteur_tags %}
            <div style="padding: 1rem;">
                <h3>Service tag - default (carte/list/acteur detail)</h3>
                <p>Uses action.groupe_action - is_formulaire is not set (defaults to False)</p>
                {% service_tag text=action.libelle action=action %}
            </div>
            """
        ).render(Context(context_default))

        formulaire_html = Template(
            """
            {% load acteur_tags %}
            <div style="padding: 1rem;">
                <h3>Service tag - formulaire mode</h3>
                <p>Uses action directly with reduced opacity - is_formulaire=True</p>
                {% service_tag text=action.libelle action=action %}
            </div>
            """
        ).render(Context(context_formulaire))

        return default_html + formulaire_html


class FiltresPreview(LookbookPreview):
    """
    Previews for filter label components
    """

    @component_docs("ui/components/filtres/bonus/label.md")
    def label_bonus(self, **kwargs):
        return render_to_string("ui/components/formulaire/filtres/bonus/label.html")

    @component_docs("ui/components/filtres/ess/label.md")
    def label_ess(self, **kwargs):
        return render_to_string("ui/components/filtres/ess/label.html")

    @component_docs("ui/components/filtres/reparacteurs/label.md")
    def label_reparacteurs(self, **kwargs):
        return render_to_string(
            "ui/components/formulaire/filtres/reparacteurs/label.html"
        )


class ModalForm(forms.Form):
    button_only = forms.BooleanField(
        label="Seulement le bouton",
        help_text="Ne doit rien afficher, mais en inspectant la preview, on doit retrouver le tag <button>",
    )
    modal_only = forms.BooleanField(
        label="Seulement la modal",
        help_text="Ne doit rien afficher, mais en inspectant la preview, on doit retrouver le tag <dialog>",
    )


class ModalsPreview(LookbookPreview):
    @component_docs("ui/components/modals/integration.md")
    def integration(self, **kwargs):
        return render_to_string("ui/components/modals/embed.html")

    def partage(self, **kwargs):
        return render_to_string("ui/components/modals/share.html")

    def filtres(self, **kwargs):
        from qfdmo.forms import FiltresForm, LegendeForm

        context = {"legende_form": LegendeForm(), "filtres_form": FiltresForm}
        return render_to_string("ui/components/modals/filtres.html", context)

    @register_form_class(ModalForm)
    @component_docs("ui/components/modals/infos_avec_toggle.md")
    def infos_avec_toggle(
        self, button_only=False, modal_only=False, button_text="Infos", **kwargs
    ):
        # Convert string values to boolean
        if isinstance(button_only, str):
            button_only = button_only.lower() == "true"
        if isinstance(modal_only, str):
            modal_only = modal_only.lower() == "true"

        context = {
            "button_only": button_only,
            "modal_only": modal_only,
            "button_text": button_text,
            "button_extra_classes": "fr-btn--sm",
        }

        return render_to_string("ui/components/modals/infos.html", context)

    def infos(self, **kwargs):
        return render_to_string("ui/components/modals/infos.html")


class FormulairesPreview(LookbookPreview):
    @component_docs("ui/components/formulaires/plusieurs_formulaires.md")
    def plusieurs_formulaires(self, **kwargs):
        form1 = LegendeForm(prefix="1")
        form2 = LegendeForm(prefix="2")

        template = Template(
            """
            {% load turbo_tags %}
            <form>
                {% include "ui/components/modals/filtres.html" with filtres_form=form1 id="filtres-legende" %}
                {% include "ui/components/modals/filtres.html" with filtres_form=form2 id="filtres-legende-mobile" %}
            </form>
            """
        )
        context = {"form1": form1, "form2": form2}
        return template.render(Context(context))

    def autocompletion(self, **kwargs):
        class AutocompleteForm(DsfrBaseForm):
            synonyme = forms.ModelChoiceField(
                queryset=Synonyme.objects.all(),
                widget=SynonymeAutocompleteInput(),
                help_text="pantalon, perceuse, canapé...",
                label="Indiquer un objet ",
                empty_label="",
                required=False,
            )

        form = AutocompleteForm()
        template = Template("{{ form }}")
        context = {"form": form}
        return template.render(Context(context))

    def autocomplete_search_homepage(self, **kwargs):
        """Preview of the autocomplete search form used on the homepage."""
        from qfdmd.forms import HomeSearchForm

        form = HomeSearchForm()
        template = Template(
            """
            <div class="qf-max-w-3xl qf-mx-auto qf-p-4w">
                <h2>Autocomplete Search (Homepage)</h2>
                <p class="qf-mb-2w">This autocomplete search navigates to results on selection.</p>
                {% include "ui/components/search/autocomplete_view.html" with autocomplete_search_form=form %}
            </div>
            """
        )
        context = {"form": form}
        return template.render(Context(context))

    @component_docs("ui/components/formulaires/mode_carte_liste.md")
    def mode_carte_liste(self, **kwargs):
        form = ViewModeForm()
        template = Template("{{ form }}")
        context = {"form": form}
        return template.render(Context(context))

    def autocomplete_widgets(self, **kwargs):
        """Prévisualisation de tous les types de widgets d'autocomplétion sur une seule page."""

        class AutocompleteFormExample(DsfrBaseForm):
            synonyme = forms.ModelChoiceField(
                queryset=Synonyme.objects.all(),
                widget=SynonymeAutocompleteInput(),
                help_text="pantalon, perceuse, canapé...",
                label="Autocomplétion Synonyme",
                empty_label="",
                required=False,
            )

            search = forms.CharField(
                label="Autocomplétion Recherche d'accueil",
                required=False,
                widget=HomeSearchAutocompleteInput(
                    attrs={
                        "class": "fr-input",
                        "placeholder": "pantalon, perceuse, canapé...",
                        "autocomplete": "off",
                    },
                ),
            )

        form = AutocompleteFormExample()

        template = Template(
            """
            <div class="qf-max-w-3xl qf-space-y-4w">
                <h2 class="qf-text-2xl qf-font-bold qf-mb-4w">Widgets d'autocomplétion</h2>
                <hr>

                {{ form }}
            </div>
            """
        )
        context = {
            "form": form,
        }
        return template.render(Context(context))


class PagesPreview(LookbookPreview):
    def home(self, **kwargs):
        context = {
            "request": None,
            "ASSISTANT": {"faites_decouvrir_ce_site": "Faites découvrir ce site !"},
        }
        return render_to_string("ui/pages/home.html", context)

    def produit(self, **kwargs):
        context = {"object": Synonyme.objects.first()}
        return render_to_string("ui/pages/produit.html", context)

    def acteur(self, **kwargs):
        acteur = DisplayedActeur.objects.first()
        factory = RequestFactory()
        request = factory.get("/")
        context = {
            "object": acteur,
            "request": request,
            "base_template": "ui/layout/base.html",
            "turbo": False,
        }
        return render_to_string("ui/pages/acteur.html", context)


class SnippetsPreview(LookbookPreview):
    @component_docs("ui/components/header/header.md")
    def header(self, **kwargs):
        context = {"request": None}
        return render_to_string("ui/components/header/header.html", context)

    def footer(self, **kwargs):
        return render_to_string("ui/components/footer/footer.html")

    def suggestions(self, **kwargs):
        context = {
            "heading": "Coucou",
            "suggestions": [("coucou", "google.fr"), ("youpi", "google.fr")],
        }
        return render_to_string("ui/components/suggestions/suggestions.html", context)

    def share_and_embed(self, **kwargs):
        context = {"heading": "Faites découvrir ce site"}
        return render_to_string("ui/snippets/share_and_embed.html", context)


class IframePreview(LookbookPreview):
    def carte(self, **kwargs):
        """
        # Carte

        Copiez ce script pour intégrer la carte sur votre site :

        ```html
        <script src="{base_url}/static/carte.js"></script>
        ```
        """

        template = Template(
            f"""
            <script src="{base_url}/static/carte.js"></script>
            """,
        )
        return template.render(Context({}))

    @register_form_class(CarteConfigForm)
    def carte_sur_mesure(self, carte_config=None, **kwargs):
        """
        # Carte sur mesure

        Copiez ce script pour intégrer une carte personnalisée :

        ```html
        <script src="{base_url}/static/carte.js" data-slug="cyclevia"></script>
        ```
        """
        # carte_config is returned as a string by django-lookbook where we expected
        # representing the id of a CarteConfig object.
        if isinstance(carte_config, str) and carte_config:
            carte_config = CarteConfig.objects.get(id=carte_config)

        slug = carte_config.slug if carte_config else "cyclevia"

        template = Template(
            f"""
            <script src="{base_url}/static/carte.js" data-slug="{slug}"></script>
            """,
        )

        return template.render(Context({}))

    def carte_preconfiguree(self, **kwargs):
        """
        # Carte préconfigurée

        Copiez ce script pour intégrer une carte avec filtres prédéfinis :

        ```html
        <script src="{base_url}/static/carte.js"
            data-action_displayed="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre"
            data-max-width="800px"
            data-height="720px"
            data-bounding_box="{{ 'southWest': {{'lat': 47.570401, 'lng': 1.597977 }}, 'northEast': {{ 'lat': 48.313697, 'lng': 3.059159 }}}}">
        </script>
        ```
        """

        template = Template(
            f"<script src='{base_url}/static/carte.js'"
            """data-action_displayed="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre"
            data-max-width="800px"
            data-height="720px"
            data-bounding_box="{&quot;southWest&quot;: {&quot;lat&quot;: 47.570401, &quot;lng&quot;: 1.597977}, &quot;northEast&quot;: {&quot;lat&quot;: 48.313697, &quot;lng&quot;: 3.059159}}"
            ></script>
            """,
        )

        return template.render(Context({}))

    def integrations(self, **kwargs):
        """
        # Integrations

        Copiez ce script pour intégrer une carte avec des paramètres spécifiques :

        ```html
        <script src="{base_url}/static/carte.js"
            data-action_list="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre"
            data-bounding_box="{{ 'southWest': {{'lat': 47.457526, 'lng': -0.609453 }}, 'northEast': {{ 'lat': 47.489048, 'lng': -0.51571 }}}}">
        </script>
        ```
        """

        template = Template(
            f"<script src='{base_url}/static/carte.js'"
            """ data-action_list="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre" data-bounding_box="{&quot;southWest&quot;: {&quot;lat&quot;: 47.457526, &quot;lng&quot;: -0.609453}, &quot;northEast&quot;: {&quot;lat&quot;: 47.489048, &quot;lng&quot;: -0.51571}}"></script>
            """,
        )

        return template.render(Context({}))

    def formulaire(self, **kwargs):
        """
        # Formulaire

        Copiez ce script pour intégrer le formulaire de recherche :

        ```html
        <script src="{base_url}/static/iframe.js"
            data-max_width="100%"
            data-height="720px"
            data-direction="jai"
            data-action_list="reparer|echanger|mettreenlocation|revendre"
            data-iframe_attributes='{{ "loading":"lazy", "id" : "resize" }}'>
        </script>
        ```
        """

        template = Template(
            f"<script src='{base_url}/static/iframe.js'"
            """
                data-max_width="100%"
                data-height="720px"
                data-direction="jai"
                data-action_list="reparer|echanger|mettreenlocation|revendre"
                data-iframe_attributes='{"loading":"lazy"}'>
                </script>
            """,
        )

        return template.render(Context({}))

    def assistant(self, **kwargs):
        """
        # Assistant

        Copiez ce script pour intégrer l'assistant produit/déchet :

        ```html
        <script src="{base_url}/iframe.js"></script>
        ```
        """

        template = Template(
            f"""
        <script src="{base_url}/iframe.js" data-testid='assistant'></script>
        """,
        )

        return template.render(Context({}))

    def assistant_with_epci(self, **kwargs):
        """
        # Assistant avec EPCI

        Copiez ce script pour intégrer l'assistant avec un code EPCI et objet prédéfinis :

        ```html
        <script src="{base_url}/iframe.js" data-epci="200043123" data-objet="lave-linge"></script>
        ```
        """

        template = Template(
            f"""
        <script src="{base_url}/iframe.js" data-epci="200043123" data-objet="lave-linge"></script>
        """,
        )

        return template.render(Context({}))

    def assistant_without_referrer(self, **kwargs):
        """
        # Assistant sans referrer

        Copiez ce script pour intégrer l'assistant en mode debug (sans referrer) :

        ```html
        <script src="{base_url}/iframe.js" data-debug-referrer></script>
        ```
        """

        template = Template(
            f"""
        <script src="{base_url}/iframe.js" data-debug-referrer data-testid='assistant'></script>
        """,
        )

        return template.render(Context({}))

    @register_form_class(InfotriForm)
    def infotri(self, categorie="", consigne="", avec_phrase="false", **kwargs):
        """
        # Info-tri

        Affiche un Info-tri avec les options configurables via le formulaire.

        Copiez ce script pour intégrer l'Info-tri sur votre site :

        ```html
        <script src="{base_url}/infotri/iframe.js"
                data-config="{config}"></script>
        ```
        """

        # Build config string from parameters
        params = []
        if categorie:
            params.append(f"categorie={categorie}")
        if consigne:
            params.append(f"consigne={consigne}")

        # Handle avec_phrase as boolean string
        if isinstance(avec_phrase, str):
            avec_phrase_value = avec_phrase.lower() in ["true", "1", "yes", "on"]
        else:
            avec_phrase_value = bool(avec_phrase)
        params.append(f"avec_phrase={'true' if avec_phrase_value else 'false'}")

        config = "&".join(params)

        template = Template(
            f"""
        <script src="{base_url}/infotri/iframe.js"
                data-config="{config}"></script>
        """,
        )

        return template.render(Context({}))

    def infotri_configurator(self, **kwargs):
        """
        # Configurateur Info-tri

        Affiche le configurateur Info-tri complet en iframe.

        Copiez ce script pour intégrer le configurateur :

        ```html
        <script src="{base_url}/infotri/configurateur.js"></script>
        ```
        """
        template = Template(
            f"""
        <script src="{base_url}/infotri/configurateur.js"></script>
        """,
        )

        return template.render(Context({}))


class AccessibilitePreview(LookbookPreview):
    @component_docs("ui/components/accessibilite/P01_7_3.md")
    def P01_7_3(self, **kwargs):
        return render_to_string("ui/modals/share.html")

    @component_docs("ui/components/accessibilite/P01_3_3.md")
    def P01_3_3(self, **kwargs):
        context = {"search_form": SearchForm()}
        return render_to_string("ui/components/search/view.html", context)

    @component_docs("ui/components/accessibilite/P01_10_2.md")
    def P01_10_2(self, **kwargs):
        context = {"search_form": SearchForm()}
        return render_to_string("ui/components/search/view.html", context)

    @component_docs("ui/components/accessibilite/P01_10_7.md")
    def P01_10_7(self, **kwargs):
        context = {"search_form": SearchForm()}
        return render_to_string("ui/components/search/view.html", context)

    @component_docs("ui/components/accessibilite/P01_13_8.md")
    def P01_13_8(self, **kwargs):
        template = Template(
            """
            {% load dsfr_tags %}

            <p class="fr-h2">Logo en homepage</p>
            {% include "ui/components/logo/homepage.html" %}
            <hr>
            <p class="fr-h2">Logo du header</p>
            {% include "ui/components/logo/header.html" %}
            """,
        )
        return template.render(Context({}))

    @component_docs("ui/components/accessibilite/P02_7_1__P02_7_3.md")
    def P02_7_1__P02_7_3(self, **kwargs):
        context = {
            "self": {
                "get_ancestors": [
                    {"title": "Une première page", "is_site_root": True},
                    {"title": "Une deuxième page", "is_root": False},
                ],
                "title": "Une troisième page",
            },
        }
        return render_to_string(
            "sites_faciles_content_manager/blocks/breadcrumbs.html",
            context,
        )


class TestsPreview(LookbookPreview):
    """
    Test previews for e2e tests.

    Naming convention:
    - Prefix all methods with t_{number}_ where number is incremental (t_1_, t_2_, t_3_, etc.)
    - The number represents the chronological order of test creation
    - Oldest tests have lower numbers and appear first in the class
    - When adding a new test, use the next available number and add it at the bottom
    - Keep methods ordered by their number prefix for easy navigation

    Example: t_1_referrer, t_2_carte_mode_liste_switch, t_3_ess_label_display

    Adding a new test:
    1. Create a dedicated template in templates/ui/tests/ (e.g., my_new_test.html)
    2. Add a preview method here following the naming convention (e.g., t_4_my_new_test)
    3. Create the corresponding e2e test in e2e_tests/ (usually in carte.spec.ts or dedicated file)
    4. In the e2e test, navigate to /lookbook/preview/tests/t_4_my_new_test

    Each test should be self-contained with its own template and e2e test specification.
    """

    def t_1_referrer(self, **kwargs):
        return render_to_string(
            "ui/tests/t_1_referrer.html",
        )

    def t_2_carte_mode_liste_switch(self, **kwargs):
        """Test switching between carte and liste modes with bounding box"""
        return render_to_string(
            "ui/tests/carte_mode_liste_switch.html",
            {"base_url": base_url},
        )

    def t_3_ess_label_display(self, **kwargs):
        """Test ESS label display in acteur detail panel"""
        return render_to_string(
            "ui/tests/ess_label_display.html",
        )

    def t_4_legend_filters_persistence(self, **kwargs):
        """Test legend filters persistence when switching between carte and liste modes"""
        return render_to_string(
            "ui/tests/legend_filters_persistence.html",
        )

    def t_5_rechercher_dans_zone(self, **kwargs):
        """Test search in zone button appearance and bounding box update"""
        return render_to_string(
            "ui/tests/search_in_zone_button.html",
            {"base_url": base_url},
        )

    def t_6_carte_config_bounding_box(self, **kwargs):
        """Test that bounding box from CarteConfig is correctly applied on initial load"""
        from django.contrib.gis.geos import Polygon
        from django.urls import reverse

        # Create a test CarteConfig with a bounding box
        # This bounding box covers Angers, France
        bounding_box_polygon = Polygon.from_bbox(
            (-0.609453, 47.457526, -0.51571, 47.489048)
        )

        carte_config, created = CarteConfig.objects.get_or_create(
            slug="test-bounding-box",
            defaults={
                "nom": "Test Bounding Box",
                "bounding_box": bounding_box_polygon,
            },
        )

        if not created and carte_config.bounding_box != bounding_box_polygon:
            carte_config.bounding_box = bounding_box_polygon
            carte_config.save()

        carte_config_url = reverse(
            "qfdmo:carte_custom", kwargs={"slug": "test-bounding-box"}
        )

        return render_to_string(
            "ui/tests/carte_config_bounding_box.html",
            {
                "carte_config_url": carte_config_url,
            },
        )

    def t_7_copy_controller(self, **kwargs):
        """Test copy controller functionality with clipboard and button text updates"""
        return render_to_string(
            "ui/tests/copy_controller.html",
        )

    def t_8_iframe_navigation_persistence(self, **kwargs):
        """Test that iframe-specific UI persists during navigation"""
        return render_to_string(
            "ui/tests/iframe_navigation_persistence.html",
            {"base_url": base_url},
        )
