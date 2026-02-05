import logging
import re
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, TemplateView
from queryish.rest import APIModel
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.models import Page

from core.constants import SEARCH_TERM_ID_QUERY_PARAM
from core.views import static_file_content_from
from qfdmd.forms import SearchForm
from qfdmd.models import (
    Produit,
    Synonyme,
)

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


def import_legacy_synonymes(request, id):
    """
    Import legacy synonymes as SearchTags for a ProduitPage.

    This view collects all legacy synonymes from:
    - legacy_synonymes: directly linked synonymes
    - legacy_produit: synonymes from linked legacy products

    Excluding:
    - legacy_synonymes_to_exclude: synonymes marked for exclusion

    For each collected synonyme:
    1. Create a SearchTag linked to the ProduitPage
    2. Mark the Synonyme as imported (links to the SearchTag)
    """
    from qfdmd.models import ProduitPage, SearchTag, TaggedSearchTag

    page = Page.objects.get(id=id).specific

    if not isinstance(page, ProduitPage):
        messages.error(
            request,
            "Cette action n'est disponible que pour les pages Produit.",
        )
        return redirect("wagtailadmin_pages:edit", id)

    # Collect synonymes to exclude
    excluded_synonyme_ids = set(
        page.legacy_synonymes_to_exclude.values_list("synonyme_id", flat=True)
    )

    # Collect all synonymes from legacy_synonymes
    direct_synonymes = list(
        Synonyme.objects.filter(next_wagtail_page__page=page).exclude(
            id__in=excluded_synonyme_ids
        )
    )

    # Collect all synonymes from legacy_produit (products linked to this page)
    product_synonymes = list(
        Synonyme.objects.filter(produit__next_wagtail_page__page=page).exclude(
            id__in=excluded_synonyme_ids
        )
    )

    # Combine and deduplicate
    all_synonymes = {s.id: s for s in direct_synonymes + product_synonymes}.values()

    imported_count = 0
    for synonyme in all_synonymes:
        # Skip if already imported as a SearchTag
        if synonyme.imported_as_search_tag is not None:
            continue

        # 1. Create or get SearchTag with the synonyme name
        search_tag, tag_created = SearchTag.objects.get_or_create(
            name=synonyme.nom,
            defaults={"slug": synonyme.slug},
        )

        # 2. Link the SearchTag to the ProduitPage if not already linked
        TaggedSearchTag.objects.get_or_create(
            tag=search_tag,
            content_object=page,
        )

        # 3. Mark the Synonyme as imported
        synonyme.imported_as_search_tag = search_tag
        synonyme.save(update_fields=["imported_as_search_tag"])

        imported_count += 1

    if imported_count > 0:
        messages.success(
            request,
            f"{imported_count} synonyme(s) de recherche importé(s) avec succès.",
        )
    else:
        messages.info(
            request,
            "Aucun nouveau synonyme à importer. "
            "Tous les synonymes sont déjà présents ou aucun synonyme legacy n'est lié.",
        )

    return redirect("wagtailadmin_pages:edit", id)


@cache_control(max_age=31536000)
def get_assistant_script(request):
    return static_file_content_from("embed/assistant.js")


SEARCH_VIEW_TEMPLATE_NAME = "ui/components/search/view.html"


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
        form.search()
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


def get_homepage():
    return Page.objects.live().get(depth=2).specific


@method_decorator(cache_control(max_age=60 * 15), name="dispatch")
@method_decorator(vary_on_headers("logged-in", "iframe"), name="dispatch")
class HomeView(AssistantBaseView, TemplateView):
    template_name = "ui/pages/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(page=get_homepage())

        return context


class SynonymeDetailView(AssistantBaseView, DetailView):
    template_name = "ui/pages/produit.html"
    model = Synonyme

    def _build_redirect_url(self, request: HttpRequest, base_url: str) -> str:
        """Build redirect URL, preserving search_term_id if present."""
        search_term_id = request.GET.get(SEARCH_TERM_ID_QUERY_PARAM)
        if search_term_id:
            return f"{base_url}?{SEARCH_TERM_ID_QUERY_PARAM}={search_term_id}"
        return base_url

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        synonyme = self.get_object()

        # First, check if the synonyme has a direct redirection
        try:
            synonyme_intermediate_page = synonyme.next_wagtail_page
            redirect_url = self._build_redirect_url(
                request, synonyme_intermediate_page.page.url
            )
            return redirect(redirect_url)
        except Synonyme.next_wagtail_page.RelatedObjectDoesNotExist:
            pass

        # If no direct redirection, check if produit has redirection
        try:
            intermediate_page = synonyme.produit.next_wagtail_page
            synonyme_can_be_redirected = (
                not hasattr(synonyme, "should_not_redirect_to")
                or synonyme.should_not_redirect_to.page != intermediate_page.page
            )
            if synonyme_can_be_redirected:
                redirect_url = self._build_redirect_url(
                    request, intermediate_page.page.url
                )
                return redirect(redirect_url)
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


class BonusViewSet(ModelViewSet):
    model = Bonus
    form_fields = ["title", "montant_min", "montant_max"]
    icon = "tag"
    list_filter = ["montant_min", "montant_max"]
    add_to_admin_menu = True
    copy_view_enabled = False
    inspect_view_enabled = True


bonus_viewset = BonusViewSet("bonus")
