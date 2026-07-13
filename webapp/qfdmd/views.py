import logging
from typing import Any, override
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import django_filters
from django.contrib import messages
from django.contrib.admin.utils import quote
from django.db import (
    DataError,
    IntegrityError,
    OperationalError,
    connection,
    transaction,
)
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail.views import serve as wagtail_serve
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView, TemplateView
from modelsearch.index import insert_or_update_object
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.ui.tables import BulkActionsCheckboxColumn
from wagtail.admin.views.generic.models import IndexView as ModelIndexView
from wagtail.admin.views.pages.listing import IndexView
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets.pages import PageListingViewSet
from modelsearch.query import Fuzzy
from wagtail.models import Page

from core.constants import SEARCH_TERM_ID_QUERY_PARAM
from core.views import static_file_content_from
from qfdmd.legacy_migration import (
    MigrationError,
    get_or_create_legacy_index_page,
    migrate_produit,
    revert_produit_migration,
)
from qfdmd.models import (
    HomePage,
    Produit,
    ProduitPage,
    SearchTag,
    Synonyme,
    TaggedSearchTag,
)
from qfdmd.utils import see_more_button
from search.models import SearchTerm
from search.score_breakdown import compute_breakdown

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

    other_pages_synonyme_ids = set(
        Synonyme.objects.filter(next_wagtail_page__isnull=False)
        .exclude(next_wagtail_page__page=page)
        .values_list("id", flat=True)
    )

    product_synonymes = list(
        Synonyme.objects.filter(produit__next_wagtail_page__page=page)
        .exclude(id__in=excluded_synonyme_ids)
        .exclude(id__in=other_pages_synonyme_ids)
    )

    return list(
        {
            synonyme.id: synonyme for synonyme in direct_synonymes + product_synonymes
        }.values()
    )


# taggit's TagBase imposes max_length=100 on both name and slug. Legacy
# Synonyme records can have longer values, so we truncate to fit and keep
# the import alive instead of bubbling a DataError up to the user.
_SEARCH_TAG_MAX_LENGTH = 100

# How many names to show in the "first N items" preview of warning messages
# before collapsing the tail into a "+overflow" count.
_PREVIEW_LIMIT = 5


def _preview_names(names: list[str]) -> str:
    """Render a comma-joined preview of up to _PREVIEW_LIMIT names, with a
    trailing "… (+N)" when more were skipped."""
    head = ", ".join(names[:_PREVIEW_LIMIT])
    if len(names) > _PREVIEW_LIMIT:
        return f"{head}… (+{len(names) - _PREVIEW_LIMIT})"
    return head


class _EmptySlugError(Exception):
    """Raised when a legacy Synonyme has an empty slug.

    Synonyme.slug is an AutoSlugField populated from .nom, so an empty
    value points at a malformed legacy record (e.g. nom containing only
    punctuation). We refuse to import it instead of silently coalescing
    to "" \u2014 which would otherwise collide with every other empty-slug
    tag and mask the data problem.
    """


def _import_one_synonyme(page, synonyme, tracking_field="imported_as_search_tag"):
    """Import a single Synonyme as a SearchTag, linked to the given page.

    Wrapped in a savepoint by the caller so a per-synonyme failure rolls
    back only this iteration. Raises any DB exception so the caller can
    record it.

    ``tracking_field`` is the Synonyme field stamped with the created
    SearchTag: ``imported_as_search_tag`` for the manual import,
    ``legacy_imported_as_search_tag`` for the automatic migration
    (migrate_produits_legacy command).

    Returns True when the synonyme's name or slug had to be truncated to
    fit SearchTag's 100-char limit (the caller surfaces those to the user
    so they can rename the legacy record).

    Raises _EmptySlugError when synonyme.slug is missing \u2014 the caller
    surfaces those separately so the admin can fix the underlying record.
    """
    # Replace commas with fullwidth commas to prevent taggit from splitting
    # the tag name on commas during admin round-trips.
    tag_name_full = synonyme.nom.replace(", ", "\uff0c").replace(",", "\uff0c")
    slug_full = synonyme.slug or ""
    if not slug_full:
        raise _EmptySlugError(synonyme.nom)
    tag_name = tag_name_full[:_SEARCH_TAG_MAX_LENGTH]
    slug = slug_full[:_SEARCH_TAG_MAX_LENGTH]
    truncated = len(tag_name_full) > _SEARCH_TAG_MAX_LENGTH or (
        len(slug_full) > _SEARCH_TAG_MAX_LENGTH
    )

    search_tag = SearchTag.objects.filter(slug=slug).first()
    if search_tag is None:
        search_tag = SearchTag.objects.filter(name=tag_name).first()
    if search_tag is None:
        search_tag = SearchTag.objects.create(name=tag_name, slug=slug)

    if search_tag.legacy_existing_synonyme is None:
        search_tag.legacy_existing_synonyme = synonyme
        search_tag.save(update_fields=["legacy_existing_synonyme"])

    TaggedSearchTag.objects.get_or_create(
        tag=search_tag,
        content_object=page,
    )

    # Re-index now that the tag is linked to the page, since the post_save
    # signal fired before the TaggedSearchTag existed and get_indexed_objects
    # excluded the orphan tag.
    insert_or_update_object(search_tag)

    if getattr(synonyme, tracking_field) is None:
        setattr(synonyme, tracking_field, search_tag)
        synonyme.save(update_fields=[tracking_field])

    return truncated


def _execute_import(page, all_synonymes, tracking_field="imported_as_search_tag"):
    """Execute the import of legacy synonymes as SearchTags.

    Each synonyme is imported in its own savepoint: a failure on one
    (collision, malformed data) rolls back only that iteration and the
    rest of the import proceeds. Returns a (failed, truncated, empty_slug)
    tuple of name lists so the caller can warn the user about each
    category.
    """
    failed = []
    truncated = []
    empty_slug = []
    for synonyme in all_synonymes:
        try:
            with transaction.atomic():
                was_truncated = _import_one_synonyme(
                    page, synonyme, tracking_field=tracking_field
                )
        except _EmptySlugError:
            logger.warning(
                "Skipped synonyme %s (id=%s): empty slug",
                synonyme.nom,
                synonyme.pk,
            )
            empty_slug.append(synonyme.nom)
        except (IntegrityError, DataError) as exc:
            logger.warning(
                "Skipped synonyme %s (id=%s) during legacy import: %s",
                synonyme.nom,
                synonyme.pk,
                exc,
            )
            failed.append(synonyme.nom)
        else:
            if was_truncated:
                logger.info(
                    "Truncated synonyme %s (id=%s) to %s chars during import",
                    synonyme.nom,
                    synonyme.pk,
                    _SEARCH_TAG_MAX_LENGTH,
                )
                truncated.append(synonyme.nom)
    return failed, truncated, empty_slug


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
            failed, truncated, empty_slug = _execute_import(page, all_synonymes)
            skipped_count = len(failed) + len(empty_slug)
            imported_count = len(all_synonymes) - skipped_count
            if imported_count:
                messages.success(
                    request,
                    f"{imported_count} synonyme(s) de recherche importé(s) "
                    f"avec succès.",
                )
            if failed:
                messages.warning(
                    request,
                    f"{len(failed)} synonyme(s) n'ont pas pu être importé(s) "
                    f"(ils sont probablement en doublon ou mal formés) : "
                    f"{_preview_names(failed)}",
                )
            if empty_slug:
                messages.warning(
                    request,
                    f"{len(empty_slug)} synonyme(s) ont été ignoré(s) car "
                    f"leur slug est vide : {_preview_names(empty_slug)}. "
                    "Vérifiez le champ « nom » du synonyme legacy puis "
                    "relancez l'import.",
                )
            if truncated:
                messages.warning(
                    request,
                    f"{len(truncated)} synonyme(s) ont été tronqué(s) à "
                    f"{_SEARCH_TAG_MAX_LENGTH} caractères (limite des "
                    f"synonymes de recherche) : {_preview_names(truncated)}. "
                    "Vous pouvez renommer le synonyme de recherche "
                    "après l'import",
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


class LegacyProduitsToMigrateIndexView(ModelIndexView):
    page_title = "Produits à migrer"

    def get_base_queryset(self):
        return Produit.objects.to_migrate().order_by("id")

    @cached_property
    def columns(self):
        return [
            BulkActionsCheckboxColumn("bulk_actions", obj_type="snippet"),
            *super().columns,
        ]


class LegacyProduitsToMigrateViewSet(ModelViewSet):
    """Produits legacy (qfdmd.Produit) pas encore migrés vers une ProduitPage.

    Listing en lecture : la migration se fait via la commande
    migrate_produits_legacy, pas depuis cette interface.
    """

    model = Produit
    icon = "doc-full-inverse"
    menu_label = "Produits à migrer"
    menu_name = "produits-legacy-a-migrer"
    name = "produits-legacy-a-migrer"
    index_view_class = LegacyProduitsToMigrateIndexView
    index_template_name = "wagtailsnippets/snippets/index.html"
    form_fields = ["nom"]
    list_display = ["nom", "id", "nb_synonymes_to_migrate"]
    search_fields = ["nom"]
    inspect_view_enabled = True
    add_to_admin_menu = False


class MigratedLegacyProduitsIndexView(IndexView):
    page_title = "Produits migrés"

    def get_base_queryset(self):
        return (
            super()
            .get_base_queryset()
            .filter(automatically_migrated_from_legacy_produit=True)
        )


class MigratedLegacyProduitsViewSet(PageListingViewSet):
    """ProduitPage créées automatiquement par migrate_produits_legacy."""

    model = ProduitPage
    icon = "doc-full-inverse"
    menu_label = "Produits migrés"
    menu_name = "produits-legacy-migres"
    name = "produits-legacy-migres"
    index_view_class = MigratedLegacyProduitsIndexView
    filterset_class = ProduitPageFilterSet


class ProduitsViewSetGroup(ViewSetGroup):
    items = (
        FamilleEtProduitsViewSet,
        ProduitsViewSet,
        FamillesViewSet,
        AMigrerViewSet,
        LegacyProduitsToMigrateViewSet,
        MigratedLegacyProduitsViewSet,
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


class AutocompleteHomeSearchView(ListView):
    """View for autocomplete search results on homepage.

    Searches using SearchTerm.objects.searchable().search().
    """

    template_name = "ui/components/search/autocomplete_results.html"

    # This limit comes from a UI/UX decision to display only
    # seven results.
    NUMBER_OF_ITEMS_DISPLAYED = 7

    SEARCH_TIMEOUT_MS = 3000

    @override
    def get_queryset(self):
        query = self.request.GET.get("q", "")
        limit = self.NUMBER_OF_ITEMS_DISPLAYED
        if not query:
            return []
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET LOCAL statement_timeout = %s", [self.SEARCH_TIMEOUT_MS]
                )
            results = SearchTerm.objects.searchable().search(
                Fuzzy(query, unaccent=True)
            )
            if getattr(self.request, "beta", False):
                results = results.annotate_score("_search_score")
            return results[:limit]
        except OperationalError:
            safe_query = query.replace("\r", "").replace("\n", "")
            logger.warning("Autocomplete search timed out for query: %r", safe_query)
            return []

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turbo_frame_id"] = self.request.GET.get("turbo_frame_id")
        results = self.get_queryset()
        context["results"] = results
        if getattr(self.request, "beta", False) and results:
            query = self.request.GET.get("q", "")
            context["score_breakdown"] = compute_breakdown(
                query, [r.pk for r in results]
            )
        return context


def get_homepage():
    if homepage := HomePage.objects.first():
        return homepage
    return Page.objects.filter(depth=2).first()


@method_decorator(cache_control(max_age=60 * 15), name="dispatch")
@method_decorator(
    vary_on_headers("logged-in", "iframe", "sec-fetch-dest"), name="dispatch"
)
class HomeView(TemplateView):
    template_name = "ui/pages/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(page=get_homepage())

        return context


class SynonymeDetailView(DetailView):
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

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx.update(
            footer_primary_button=see_more_button(self.object.get_absolute_url())
        )

        return ctx

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        synonyme = self.get_object()

        # First, check if the synonyme has a direct redirection
        try:
            synonyme_intermediate_page = synonyme.next_wagtail_page
            redirect_url = synonyme_intermediate_page.page.url
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

        # Finally, check if the produit was automatically migrated to a
        # ProduitPage by the migrate_produits_legacy command
        migrated_page = synonyme.produit.legacy_imported_as_produit_page
        if migrated_page is not None and migrated_page.live:
            synonyme_can_be_redirected = (
                not hasattr(synonyme, "should_not_redirect_to")
                or synonyme.should_not_redirect_to.page.pk != migrated_page.pk
            )
            # Guard against a redirect loop when the migrated page lives at
            # the exact same URL as the legacy synonyme (/dechet/<slug>/)
            if synonyme_can_be_redirected and migrated_page.url != request.path:
                return redirect(self._build_redirect_url(request, migrated_page.url))

        return super().get(request, *args, **kwargs)


def migrate_single_produit(request: HttpRequest, id: str) -> HttpResponse:
    """Migrate a single legacy Produit to a ProduitPage from the admin.

    GET returns to the Produit admin with an error (migration requires POST).
    POST executes the migration and redirects back with a success/error
    message.
    """
    produit = get_object_or_404(Produit, pk=id)

    if request.method != "POST":
        messages.warning(request, "La migration nécessite une confirmation POST.")
        return redirect(
            reverse(
                "wagtailsnippets_qfdmd_produit:edit",
                args=[quote(id)],
            )
        )

    try:
        index_page, _ = get_or_create_legacy_index_page()
        with transaction.atomic():
            report = migrate_produit(produit, index_page=index_page)
    except MigrationError as exc:
        messages.error(request, str(exc))
        return redirect(
            reverse(
                "wagtailsnippets_qfdmd_produit:edit",
                args=[quote(id)],
            )
        )

    page_url = reverse("wagtailadmin_pages:edit", args=[report.page.pk])
    msg = mark_safe(
        f"Produit &laquo;&nbsp;{produit.nom}&nbsp;&raquo; migr&eacute; vers la page "
        f'<a href="{page_url}">{report.page.title}</a>.'
    )
    if report.details:
        msg = mark_safe(msg + f" {report.details}")
    messages.success(request, msg)
    return redirect(
        reverse(
            "wagtailsnippets_qfdmd_produit:edit",
            args=[quote(id)],
        )
    )


def revert_single_produit(request: HttpRequest, id: str) -> HttpResponse:
    """Revert the automatic migration of a single legacy Produit.

    GET returns to the Produit admin with an error (revert requires POST).
    POST deletes the migrated ProduitPage and cleans up, then redirects
    back with a success/error message.
    """
    produit = get_object_or_404(Produit, pk=id)

    if request.method != "POST":
        messages.warning(
            request, "L'annulation de la migration nécessite une confirmation POST."
        )
        return redirect(
            reverse(
                "wagtailsnippets_qfdmd_produit:edit",
                args=[quote(id)],
            )
        )

    try:
        with transaction.atomic():
            revert_produit_migration(produit)
    except MigrationError as exc:
        messages.error(request, str(exc))
        return redirect(
            reverse(
                "wagtailsnippets_qfdmd_produit:edit",
                args=[quote(id)],
            )
        )

    messages.success(
        request,
        f"Migration de « {produit.nom} » annulée. "
        "Le produit est de nouveau éligible à la migration.",
    )
    return redirect(
        reverse(
            "wagtailsnippets_qfdmd_produit:edit",
            args=[quote(id)],
        )
    )


def sync_page_from_produit(request: HttpRequest, id: str) -> HttpResponse:
    """Synchronize a ProduitPage's body and infotri from its legacy Produit.

    GET shows a confirmation page. POST executes the sync and redirects
    back with a success/error message.
    """
    page = get_object_or_404(Page, pk=id).specific
    if not isinstance(page, ProduitPage):
        messages.error(
            request,
            "Cette action n'est disponible que pour les pages Produit.",
        )
        return redirect("wagtailadmin_pages:edit", id)

    if page.linked_legacy_produit is None:
        messages.warning(request, "Aucun produit legacy lié à cette page.")
        return redirect("wagtailadmin_pages:edit", id)

    if request.method == "POST":
        msgs = page.sync_from_legacy_produit()
        if msgs:
            messages.success(
                request,
                mark_safe(
                    "Contenu synchronisé depuis le produit legacy :<br/>"
                    + "<br/>".join(f"&bull; {m}" for m in msgs)
                ),
            )
        else:
            messages.info(request, "Aucune modification effectuée.")
        return redirect("wagtailadmin_pages:edit", id)

    return render(
        request,
        "admin/qfdmd/confirm_sync_produit.html",
        {"page": page, "produit": page.linked_legacy_produit},
    )


def dechet_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Route /dechet/<slug>/: try Wagtail first, then the legacy view.

    Automatically migrated ProduitPage live under the "dechet" Wagtail
    index page and therefore share the historic synonyme URL space. We
    first try to serve a Wagtail page at this address; if none exists
    (produit not migrated yet), we fall back to the legacy
    SynonymeDetailView.
    """
    try:
        return wagtail_serve(request, request.path)
    except Http404:
        return SynonymeDetailView.as_view()(request, slug=slug)
