import logging
import re
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView, UpdateView
from dsfr.forms import DsfrBaseForm
from queryish.rest import APIModel
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.models import Page

from core.views import static_file_content_from
from data.models.suggestion import (
    Suggestion,
    SuggestionAction,
    SuggestionCohorte,
    SuggestionStatut,
)
from qfdmd.forms import SearchForm
from qfdmd.models import Bonus, Produit, ProduitIndexPage, ReusableContent, Synonyme
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.views.adresses import TurboFormMixin

logger = logging.getLogger(__name__)


def legacy_migrate(request, id):
    page = Page.objects.get(id=id).specific
    if not page.produit and not page.synonyme and not page.infotri:
        messages.warning(
            request,
            "La page n'a aucun produit ou synonyme rattaché."
            "Aucune migration ne sera effectuée.",
        )
    else:
        page.build_streamfield_from_legacy_data()
        messages.info(
            request,
            f"La page a bien été migrée à partir de {page.produit or page.synonyme}",
        )

    return redirect("wagtailadmin_pages:edit", id)


@cache_control(max_age=31536000)
def get_assistant_script(request):
    return static_file_content_from("embed/assistant.js")


SEARCH_VIEW_TEMPLATE_NAME = "ui/components/search/view.html"


class ActeurContribForm(DsfrBaseForm, ModelForm):
    class Meta:
        model = DisplayedActeur
        fields = ["nom", "adresse", "description", "horaires_description"]


class DisplayedActeurUpdateView(TurboFormMixin, UpdateView):
    model = DisplayedActeur
    form_class = ActeurContribForm
    template_name = "ui/forms/acteur_contrib_form.html"
    success_url = "qfdmd:contrib"

    @transaction.atomic
    def _create_suggestion(self, request: HttpRequest, change_form: ActeurContribForm):
        suggestion_cohorte, created = SuggestionCohorte.objects.get_or_create(
            identifiant_action="CONTRIBUTION",
            identifiant_execution=request.session.session_key,
            type_action=SuggestionAction.CONTRIBUTION,
            statut=SuggestionStatut.AVALIDER,
        )
        fields = change_form.fields
        acteur = change_form.instance

        # TODO: replace
        # acteur_from_db = DisplayedActeur.objects.get(
        #     identifiant_unique=acteur.identifiant_unique
        # )
        acteur_from_db = DisplayedActeur.objects.last()

        contexte = {}
        suggestion = {}
        for field in fields:
            if getattr(acteur_from_db, field) != getattr(acteur, field):
                contexte[field] = getattr(acteur_from_db, field)
                suggestion[field] = getattr(acteur, field)

        Suggestion.objects.create(
            suggestion_cohorte=suggestion_cohorte,
            statut=SuggestionStatut.ATRAITER,
            contexte=contexte,
            suggestion=suggestion,
        )

    def form_valid(self, form: ActeurContribForm) -> HttpResponse:
        # Create suggestion
        self._create_suggestion(self.request, form)
        context = self.get_context_data(form=form, object=self.object)
        return self.render_to_response(context)


def search_view(request) -> HttpResponse:
    prefix_key = next(
        (key for key in request.GET.dict().keys() if key.endswith("-id")), ""
    )
    form_kwargs = {}

    if prefix := request.GET[prefix_key]:
        form_kwargs.update(prefix=prefix, initial={"id": prefix})

    form = SearchForm(request.GET, **form_kwargs)
    context = {"prefix": form_kwargs, "prefix_key": prefix_key}
    template_name = SEARCH_VIEW_TEMPLATE_NAME

    if form.is_valid():
        form.search(request.beta)
        context.update(search_form=form)

    return render(request, template_name, context=context)


class AssistantBaseView:
    """Base view that provides templates used on all pages.
    It needs to be used by all views of the Assistant as it
    handles a redirect that prevents accessing a produit
    with a Carte domain name.

    TODO: move to a middleware
    """

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@method_decorator(cache_control(max_age=60 * 15), name="dispatch")
@method_decorator(vary_on_headers("logged-in", "iframe"), name="dispatch")
class HomeView(AssistantBaseView, ListView):
    template_name = "ui/pages/home.html"
    model = Suggestion

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            accordion={
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
            }
        )

        if self.request.beta:
            # The ProduitIndexPage is unique and is the future homepage.
            # It holds a body field that renders DSFR blocks.
            # At the moment it is only available to beta testers
            # but once it will be release to all users, the current homeview
            # will be deprecated and the context will be directly pulled from
            # the Wagtail page.
            context.update(page=ProduitIndexPage.objects.first())

        return context


class SynonymeDetailView(AssistantBaseView, DetailView):
    template_name = "ui/pages/produit.html"
    model = Synonyme

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.beta or settings.REDIRECT_LEGACY_PRODUIT_TO_WAGTAIL_PAGES:
            synonyme = self.get_object()
            try:
                intermediate_page = synonyme.produit.next_wagtail_page
                synonyme_can_be_redirected = (
                    not hasattr(synonyme, "should_not_redirect_to")
                    or synonyme.should_not_redirect_to.page != intermediate_page.page
                )
                if synonyme_can_be_redirected:
                    return redirect(intermediate_page.page.url)
            except Produit.next_wagtail_page.RelatedObjectDoesNotExist:
                pass

        return super().get(request, *args, **kwargs)


# WAGTAIL
# =======


class WagtailBlock(APIModel):
    class Meta:
        base_url = "https://pokeapi.co/api/v2/pokemon/"
        detail_url = "https://pokeapi.co/api/v2/pokemon/%s/"
        fields = ["id", "name"]
        pagination_style = "offset-limit"
        verbose_name_plural = "pokemon"

    @classmethod
    def from_query_data(cls, data):
        return cls(
            id=int(
                re.match(
                    r"https://pokeapi.co/api/v2/pokemon/(\d+)/", data["url"]
                ).group(1)
            ),
            name=data["name"],
        )

    @classmethod
    def from_individual_data(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
        )

    def __str__(self):
        return self.name


class BlockChooserViewSet(ChooserViewSet):
    model = WagtailBlock
    choose_one_text = "Choisir un bloc"
    choose_another_text = "Choisir un autre bloc"


pokemon_chooser_viewset = BlockChooserViewSet("pokemon_chooser")


class ReusableContentViewSet(ModelViewSet):
    model = ReusableContent
    form_fields = ["title", "genre", "nombre"]
    icon = "resubmit"
    add_to_admin_menu = True
    copy_view_enabled = True
    inspect_view_enabled = True


class BonusViewSet(ModelViewSet):
    model = Bonus
    form_fields = ["title", "montant_min", "montant_max"]
    icon = "tag"
    list_filter = ["montant_min", "montant_max"]
    add_to_admin_menu = True
    copy_view_enabled = False
    inspect_view_enabled = True


reusable_content_viewset = ReusableContentViewSet("contenu-reutilisable")
bonus_viewset = BonusViewSet("bonus")
