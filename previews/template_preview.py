# Ignore line length recommandations from flake8
# flake8: noqa: E501
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django_lookbook.preview import LookbookPreview

from qfdmd.models import Suggestion, Synonyme


class ComponentsPreview(LookbookPreview):
    def button(self, **kwargs):
        context = {"href": "google.fr", "text": "test"}
        return render_to_string("components/button.html", context)

    def code(self, **kwargs):
        context = {
            "script": '<script src="https://quefairedemesdechets.ademe.local/iframe.js"></script>'
        }
        return render_to_string("components/code/code.html", context)

    def logo_animated(self, **kwargs):
        return render_to_string("components/logo/animated.html")

    def logo_homepage(self, **kwargs):
        return render_to_string("components/logo/homepage.html")


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
            <script src="{settings.ASSISTANT["BASE_URL"]}/static/carte.js"></script>
            """,
        )
        return template.render(Context({}))

    def carte_sur_mesure(self, **kwargs):
        template = Template(
            f"""
            <script src="{settings.ASSISTANT["BASE_URL"]}/static/carte.js" data-slug="cyclevia"></script>
            """,
        )

        return template.render(Context({}))

    def carte_preconfiguree(self, **kwargs):
        template = Template(
            f"<script src='{settings.ASSISTANT['BASE_URL']}/static/carte.js'"
            """data-action_displayed="preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre"
            data-max-width="800px"
            data-height="720px"
            data-bounding_box="{&quot;southWest&quot;: {&quot;lat&quot;: 47.570401, &quot;lng&quot;: 1.597977}, &quot;northEast&quot;: {&quot;lat&quot;: 48.313697, &quot;lng&quot;: 3.059159}}"
            ></script>
            """
        )

        return template.render(Context({}))

    def formulaire(self, **kwargs):
        template = Template(
            f"<script src='{settings.LVAO['BASE_URL']}/static/iframe.js'"
            """
                data-max_width="100%"
                data-height="720px"
                data-direction="jai"
                data-first_dir="jai"
                data-action_list="reparer|echanger|mettreenlocation|revendre"
                data-iframe_attributes='{"loading":"lazy", "id" : "resize" }'>
                </script>
            """
        )

        return template.render(Context({}))

    def assistant(self, **kwargs):
        template = Template(
            f"""
        <script src="{settings.ASSISTANT["BASE_URL"]}/iframe.js" data-testid='assistant'></script>
        """
        )

        return template.render(Context({}))

    def assistant_without_referrer(self, **kwargs):
        template = Template(
            f"""
        <script src="{settings.ASSISTANT["BASE_URL"]}/iframe.js" data-debug-referrer data-testid='assistant'></script>
        """
        )

        return template.render(Context({}))
