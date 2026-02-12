import logging
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import django_filters
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, TemplateView
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.views.pages.listing import IndexView
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.models import Page

from core.constants import SEARCH_TERM_ID_QUERY_PARAM
from core.views import static_file_content_from
from qfdmd.forms import SearchForm
from qfdmd.models import (
    Produit,
    ProduitPage,
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


def _collect_synonymes_for_page(page):
    """Collect all synonymes eligible for import, minus exclusions."""
    excluded_synonyme_ids = set(
        page.legacy_synonymes_to_exclude.values_list("synonyme_id", flat=True)
    )

    direct_synonymes = list(
        Synonyme.objects.filter(next_wagtail_page__page=page).exclude(
            id__in=excluded_synonyme_ids
        )
    )

    product_synonymes = list(
        Synonyme.objects.filter(produit__next_wagtail_page__page=page).exclude(
            id__in=excluded_synonyme_ids
        )
    )

    return list(
        {
            synonyme.id: synonyme for synonyme in direct_synonymes + product_synonymes
        }.values()
    )


def _execute_import(page, all_synonymes):
    """Execute the import of legacy synonymes as SearchTags."""
    from qfdmd.models import (
        SearchTag,
        TaggedSearchTag,
    )

    for synonyme in all_synonymes:
        tag_name = synonyme.nom.lower()

        search_tag = SearchTag.objects.filter(slug=synonyme.slug).first()
        if search_tag is None:
            search_tag = SearchTag.objects.filter(name=tag_name).first()
        if search_tag is None:
            search_tag = SearchTag.objects.create(name=tag_name, slug=synonyme.slug)

        if search_tag.legacy_existing_synonyme is None:
            search_tag.legacy_existing_synonyme = synonyme
            search_tag.save(update_fields=["legacy_existing_synonyme"])

        TaggedSearchTag.objects.get_or_create(
            tag=search_tag,
            content_object=page,
        )

        if synonyme.imported_as_search_tag is None:
            synonyme.imported_as_search_tag = search_tag
            synonyme.save(update_fields=["imported_as_search_tag"])


def import_legacy_synonymes(request, id):
    """
    Import legacy synonymes as SearchTags for a ProduitPage.

    GET: shows a confirmation page listing the synonymes to import.
    POST: executes the import and redirects to the page editor.
    """
    page = Page.objects.get(id=id).specific

    if not isinstance(page, ProduitPage):
        messages.error(
            request,
            "Cette action n'est disponible que pour les pages Produit.",
        )
        return redirect("wagtailadmin_pages:edit", id)

    if page.migree_depuis_synonymes_legacy:
        messages.warning(
            request,
            "La migration des synonymes a déjà été effectuée pour cette page.",
        )
        return redirect("wagtailadmin_pages:edit", id)

    all_synonymes = _collect_synonymes_for_page(page)

    if request.method == "POST":
        if all_synonymes:
            _execute_import(page, all_synonymes)
            messages.success(
                request,
                f"{len(all_synonymes)} synonyme(s) de recherche importé(s) "
                f"avec succès.",
            )
        else:
            messages.info(
                request,
                "Aucun nouveau synonyme à importer.",
            )
        page.migree_depuis_synonymes_legacy = True
        page.save(update_fields=["migree_depuis_synonymes_legacy"])
        return redirect("wagtailadmin_pages:edit", id)

    return render(
        request,
        "admin/qfdmd/confirm_import_synonymes.html",
        {
            "page": page,
            "synonymes": all_synonymes,
            "synonyme_count": len(all_synonymes),
        },
    )


# Wagtail admin viewsets


class MigrationStatusFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "choices",
            [
                ("done", "Migrées"),
                ("pending", "À migrer"),
            ],
        )
        kwargs.setdefault("label", "Statut migration")
        kwargs.setdefault("empty_label", "Tous")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value == "done":
            return qs.filter(migree_depuis_synonymes_legacy=True)
        if value == "pending":
            return qs.filter(migree_depuis_synonymes_legacy=False)
        return qs


class TypeProduitFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "choices",
            [
                ("famille", "Familles"),
                ("produit", "Produits"),
            ],
        )
        kwargs.setdefault("label", "Type")
        kwargs.setdefault("empty_label", "Tous")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value == "famille":
            return qs.filter(est_famille=True)
        if value == "produit":
            return qs.filter(est_famille=False)
        return qs


class ProduitPageFilterSet(WagtailFilterSet):
    migration_status = MigrationStatusFilter()
    type_produit = TypeProduitFilter()

    class Meta:
        model = ProduitPage
        fields = []


class MigrationOnlyFilterSet(WagtailFilterSet):
    migration_status = MigrationStatusFilter()

    class Meta:
        model = ProduitPage
        fields = []


class FamilleEtProduitsIndexView(IndexView):
    page_title = "Familles et produits"


class FamilleEtProduitsViewSet(PageListingViewSet):
    model = ProduitPage
    icon = "doc-full-inverse"
    menu_label = "Familles et produits"
    menu_name = "famille-et-produits"
    name = "famille-et-produits"
    index_view_class = FamilleEtProduitsIndexView
    filterset_class = ProduitPageFilterSet


class ProduitsIndexView(IndexView):
    page_title = "Produits"

    def get_base_queryset(self):
        return super().get_base_queryset().filter(est_famille=False)


class ProduitsViewSet(PageListingViewSet):
    model = ProduitPage
    icon = "doc-full-inverse"
    menu_label = "Produits"
    menu_name = "produits"
    name = "produits"
    index_view_class = ProduitsIndexView
    filterset_class = MigrationOnlyFilterSet


class FamillesIndexView(IndexView):
    page_title = "Familles"

    def get_base_queryset(self):
        return super().get_base_queryset().filter(est_famille=True)


class FamillesViewSet(PageListingViewSet):
    model = ProduitPage
    icon = "doc-full-inverse"
    menu_label = "Familles"
    menu_name = "familles"
    name = "familles"
    index_view_class = FamillesIndexView
    filterset_class = MigrationOnlyFilterSet


class AMigrerIndexView(IndexView):
    page_title = "Produits/familles à migrer"

    def get_base_queryset(self):
        return super().get_base_queryset().filter(migree_depuis_synonymes_legacy=False)


class AMigrerViewSet(PageListingViewSet):
    model = ProduitPage
    icon = "doc-full-inverse"
    menu_label = "Produits/familles à migrer"
    menu_name = "a-migrer"
    name = "a-migrer"
    index_view_class = AMigrerIndexView
    filterset_class = ProduitPageFilterSet


class ProduitsViewSetGroup(ViewSetGroup):
    items = (
        FamilleEtProduitsViewSet,
        ProduitsViewSet,
        FamillesViewSet,
        AMigrerViewSet,
    )
    menu_icon = "doc-full-inverse"
    menu_label = "Produits"
    menu_name = "produits"
    menu_order = 250


# Frontend views


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
        if not search_term_id:
            return base_url
        parsed = urlparse(base_url)
        params = parse_qsl(parsed.query)
        params.append((SEARCH_TERM_ID_QUERY_PARAM, search_term_id))
        return urlunparse(parsed._replace(query=urlencode(params)))

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
