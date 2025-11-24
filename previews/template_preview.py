# Ignore line length recommandations from flake8
# flake8: noqa: E501
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.template import Context, Template
from django.template.loader import render_to_string
from django_lookbook.preview import LookbookPreview
from django_lookbook.utils import register_form_class
from dsfr.forms import DsfrBaseForm

from qfdmd.forms import SearchForm
from qfdmd.models import Suggestion, Synonyme
from qfdmo.forms import (
    LegendeForm,
    NextAutocompleteInput,
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


def load_component_docs(template_path):
    """
    Load markdown documentation for a component template.

    Looks for a .md file alongside the .html template file.
    Returns the markdown content if found, otherwise returns None.

    Example:
        template_path = "ui/components/button.html"
        -> looks for templates/ui/components/button.md
    """
    base_dir = Path(settings.BASE_DIR)
    templates_dir = base_dir / "templates"

    # Convert template path to markdown path
    md_path = templates_dir / template_path.replace(".html", ".md")

    if md_path.exists():
        return md_path.read_text()
    return None


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
        from django.core.paginator import Paginator
        from django.test import RequestFactory

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
            "map_container_id": "carte",
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
                widget=NextAutocompleteInput(
                    search_view="autocomplete_synonyme",
                    limit=10,
                ),
                help_text="pantalon, perceuse, canapé...",
                label="Indiquer un objet ",
                empty_label="",
                required=False,
            )

        form = AutocompleteForm()
        template = Template("{{ form }}")
        context = {"form": form}
        return template.render(Context(context))

    @component_docs("ui/components/formulaires/mode_carte_liste.md")
    def mode_carte_liste(self, **kwargs):
        form = ViewModeForm()
        template = Template("{{ form }}")
        context = {"form": form}
        return template.render(Context(context))


class PagesPreview(LookbookPreview):
    def home(self, **kwargs):
        context = {
            "request": None,
            "object_list": [
                Suggestion(produit=Synonyme.objects.first()),
                Suggestion(produit=Synonyme.objects.last()),
            ],
            "accordion": {
                "id": "professionels",
                "title": "Je suis un professionnel",
                "content": "Actuellement, l’ensemble des recommandations ne concerne "
                "que les particuliers. Pour des informations à destination des "
                "professionnels, veuillez consulter le site "
                "<a href='https://economie-circulaire.ademe.fr/dechets-activites-economiques'"
                "target='_blank' rel='noreferrer' "
                "title='Économie Circulaire ADEME - Nouvelle fenêtre'>"
                "https://economie-circulaire.ademe.fr/dechets-activites-economiques"
                "</a>.",
            },
            "ASSISTANT": {"faites_decouvrir_ce_site": "Faites découvrir ce site !"},
        }
        return render_to_string("ui/pages/home.html", context)

    def produit(self, **kwargs):
        context = {"object": Synonyme.objects.first()}
        return render_to_string("ui/pages/produit.html", context)


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
        template = Template(
            f"""
            <script src="{settings.BASE_URL}/static/carte.js"></script>
            """,
        )
        return template.render(Context({}))

    def carte_sur_mesure(self, **kwargs):
        template = Template(
            f"""
            <script src="{settings.BASE_URL}/static/carte.js" data-slug="cyclevia"></script>
            """,
        )

        return template.render(Context({}))

    def carte_preconfiguree(self, **kwargs):
        template = Template(
            f"<script src='{settings.BASE_URL}/static/carte.js'"
            """data-action_displayed="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre"
            data-max-width="800px"
            data-height="720px"
            data-bounding_box="{&quot;southWest&quot;: {&quot;lat&quot;: 47.570401, &quot;lng&quot;: 1.597977}, &quot;northEast&quot;: {&quot;lat&quot;: 48.313697, &quot;lng&quot;: 3.059159}}"
            ></script>
            """,
        )

        return template.render(Context({}))

    def formulaire(self, **kwargs):
        template = Template(
            f"<script src='{settings.BASE_URL}/static/iframe.js'"
            """
                data-max_width="100%"
                data-height="720px"
                data-direction="jai"
                data-action_list="reparer|echanger|mettreenlocation|revendre"
                data-iframe_attributes='{"loading":"lazy", "id" : "resize" }'>
                </script>
            """,
        )

        return template.render(Context({}))

    def assistant(self, **kwargs):
        template = Template(
            f"""
        <script src="{settings.BASE_URL}/iframe.js" data-testid='assistant'></script>
        """,
        )

        return template.render(Context({}))

    def assistant_with_epci(self, **kwargs):
        template = Template(
            f"""
        <script src="{settings.BASE_URL}/iframe.js" data-epci="200043123" data-objet="lave-linge"></script>
        """,
        )

        return template.render(Context({}))

    def assistant_without_referrer(self, **kwargs):
        template = Template(
            f"""
        <script src="{settings.BASE_URL}/iframe.js" data-debug-referrer data-testid='assistant'></script>
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
