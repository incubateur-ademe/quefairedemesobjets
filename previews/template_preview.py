# Ignore line length recommandations from flake8
# flake8: noqa: E501
from django import forms
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django_lookbook.preview import LookbookPreview
from django_lookbook.utils import register_form_class

from qfdmd.forms import SearchForm
from qfdmd.models import Suggestion, Synonyme
from qfdmo.models.acteur import ActeurType, DisplayedActeur, DisplayedPropositionService
from qfdmo.models.action import Action
from qfdmo.models.config import CarteConfig


class SynonymeForm(forms.Form):
    """
    This is to show how to add parameter editor to preview synonyme in heading
    """

    synonyme = forms.CharField(
        label="Synonyme",
        max_length=100,
        help_text="Entrez le nom d'un synonyme",
        initial="",
    )


class PinPointForm(forms.Form):
    action = forms.ModelChoiceField(
        queryset=Action.objects.all(),
        label="Action",
        to_field_name="code",
        help_text="Sélectionnez une action",
        initial=Action.objects.get(code="reparer"),
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


class ComponentsPreview(LookbookPreview):
    @register_form_class(PinPointForm)
    def acteur_pinpoint(
        self,
        action=Action.objects.get(code="reparer"),
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
            "force_visible": True,  # Only to display ir it the lookbook
        }
        template = Template(
            """
            {% load qfdmo_tags %}
            {% acteur_pinpoint_tag acteur=acteur direction=direction action_list=action_list carte=carte carte_config=carte_config sous_categorie_id=sc_id %}
            """
        )
        return template.render(Context(context))

    def button(self, **kwargs):
        context = {"href": "google.fr", "text": "test"}
        return render_to_string("components/button.html", context)

    def code(self, **kwargs):
        context = {
            "script": '<script src="https://quefairedemesdechets.ademe.local/iframe.js"></script>',
        }
        return render_to_string("components/code/code.html", context)

    def logo(self, **kwargs):
        return render_to_string("components/logo/header.html")

    def logo_homepage(self, **kwargs):
        return render_to_string("components/logo/homepage.html")

    def produit_legacy_heading(self, **kwargs):
        context = {"title": "Coucou !"}
        return render_to_string("components/produit/legacy_heading.html", context)

    @register_form_class(SynonymeForm)
    def produit_heading(self, synonyme=None, **kwargs):
        context = {"title": "Coucou !"}

        if synonyme:
            context.update(synonyme=synonyme)

        return render_to_string("components/produit/heading.html", context)

    @register_form_class(SynonymeForm)
    def produit_heading_family(self, synonyme=None, **kwargs):
        context = {"label": "youpi", "title": "Coucou !"}

        if synonyme:
            context.update(synonyme=synonyme)

        return render_to_string("components/produit/heading_family.html", context)


class ModalsPreview(LookbookPreview):
    def embed(self, **kwargs):
        """
        # Modal de partage
        La modal ci-dessous ne contient pas de code car celle-ci est
        générée via le contexte et un template tag.

        ## TODO
        - [ ] Générer un contexte fake dans Django Lookbook
        """
        return render_to_string("modals/embed.html")

    def share(self, **kwargs):
        return render_to_string("modals/share.html")


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
        return render_to_string("pages/home.html", context)

    def produit(self, **kwargs):
        context = {"object": Synonyme.objects.first()}
        return render_to_string("pages/produit.html", context)


class SnippetsPreview(LookbookPreview):
    def header(self, **kwargs):
        """
        `includes/header.html` is a partial template, we can write preview for it in this way.

        **Markdown syntax is supported in docstring**
        """
        context = {"request": None}
        return render_to_string("components/header/header.html", context)

    def footer(self, **kwargs):
        return render_to_string("components/footer/footer.html")

    def suggestions(self, **kwargs):
        context = {
            "heading": "Coucou",
            "suggestions": [("coucou", "google.fr"), ("youpi", "google.fr")],
        }
        return render_to_string("components/suggestions/suggestions.html", context)

    def share_and_embed(self, **kwargs):
        context = {"heading": "Faites découvrir ce site"}
        return render_to_string("snippets/share_and_embed.html", context)


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
                data-first_dir="jai"
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
    def P01_7_3(self, **kwargs):
        """
        # P01 7.3
        ## Retour
        "Les composants suivants ne sont pas contrôlables au clavier :
        1. Dans la modale de partage, les liens et le bouton ne sont
        pas accessibles au clavier : retirer leur attribut tabindex=""-1

        ## À vérifier
        - [ ] En utilisant la touche tab, on peut naviguer dans les boutons de la modale de partage
        """
        return render_to_string("modals/share.html")

    def P01_3_3(self, **kwargs):
        """
        # P01 3.3
        ## Retour
        "Le rapport de contraste entre les couleurs d’un composant d’interface et son arrière-plan est insuffisant, exemple :
        - le formulaire de recherche
        - les images des boutons d'intégration de l'outil, de partage et de contact

        Le rapport de contraste entre les couleurs d'un composant d'interface et son arrière-plan doit être d'au moins 3:1."

        ## À vérifier :
        - [ ] Le contour de la recherche doit être en couleur #53918C
        """
        context = {"search_form": SearchForm()}
        return render_to_string("components/search/view.html", context)

    def P01_10_2(self, **kwargs):
        """
        # P01 10.2
        ## Retour
        Lorsque l'utilisateur désactive le CSS, le contenu porteur d'information n'est plus visible, exemple :
        - le bouton de soumission du formulaire de recherche n'a pas d'intitulé, ajouter le texte "Rechercher"
        et le masquer avec la méthode sr-only*, retirer son attribut aria-label="Rechercher"

        ## À vérifier
        - [ ] Avec le CSS désactivé, le label rechercher du bouton s'affiche
        """
        context = {"search_form": SearchForm()}
        return render_to_string("components/search/view.html", context)

    def P01_10_7(self, **kwargs):
        """
        ## Retour
        Des éléments interactifs prennent le focus mais ce dernier n'est pas visible, exemple :
        - le champ de saisie du formulaire de recherche

        Soit :
        - Le style du focus natif du navigateur ne doit pas être supprimé ou dégradé
        La prise de focus est suffisamment contrastée (ratio de contraste égal ou supérieur à 3:1).

        ## À vérifier
        - [ ] Le focus du champ de recherche affiche un contour bleu bien visible
        """
        context = {"search_form": SearchForm()}
        return render_to_string("components/search/view.html", context)

    def P01_13_8(self, **kwargs):
        """
        ## Retour
        Du contenu en mouvement est déclenché automatiquement, exemple :

        - le texte "Que faire de mes... ?"


        ## À vérifier
        - [ ] Le logo est statique
        - [ ] Le logo affiche Que faire de mes objets et déchets

        """
        template = Template(
            """
            {% load dsfr_tags %}

            <p class="fr-h2">Logo en homepage</p>
            {% include "components/logo/homepage.html" %}
            <hr>
            <p class="fr-h2">Logo du header</p>
            {% include "components/logo/header.html" %}
            """,
        )
        return template.render(Context({}))

    def P02_7_1__P02_7_3(self, **kwargs):
        """
        # P02 7.1
        ## Retour
        Les composants suivants ne sont pas compatibles avec les technologies d'assistance :

        1. Le dernier élément du fil d'ariane n'a pas d'attribut href : cf. modèle de conception https://www.w3.org/WAI/ARIA/apg/patterns/breadcrumb/examples/breadcrumb/

        ## À vérifier
        - [ ] Le dernier élément du breadcrumb a un attribut href

        # P02 7.3
        ## Retour
        Les composants suivants ne sont pas contrôlables au clavier :

        1. Le dernier élément du fil d'ariane n'est pas atteignable (voir 7.1)

        ## À vérifier
        - [ ] Le dernier élément du breadcrumb est atteignable au clavier

        """
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
