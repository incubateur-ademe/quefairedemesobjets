"""Migration of legacy Produit snippets to ProduitPage, and revert.

Shared logic between the ``migrate_produits_legacy`` management command,
the bulk actions available on the Produit snippet listing and the
per-object admin views allowing to migrate / revert a single produit.
"""

from dataclasses import dataclass, field

from django.utils.text import slugify
from wagtail.log_actions import log

from qfdmd.models import (
    LEGACY_PRODUIT_INDEX_SLUG,
    PRODUIT_LEGACY_COPIED_FIELDS,
    HomePage,
    Produit,
    ProduitIndexPage,
    ProduitPage,
    TaggedSearchTag,
)


class MigrationError(Exception):
    """Raised when a Produit cannot be migrated or reverted."""


@dataclass
class MigrationReport:
    """Outcome of the migration of a single Produit."""

    page: ProduitPage
    sync_msgs: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    truncated: list[str] = field(default_factory=list)
    empty_slug: list[str] = field(default_factory=list)

    @property
    def details(self) -> str:
        parts = list(self.sync_msgs)
        if self.failed:
            parts.append(f"synonymes en échec : {', '.join(self.failed)}")
        if self.truncated:
            parts.append(f"synonymes tronqués : {', '.join(self.truncated)}")
        if self.empty_slug:
            parts.append(f"synonymes sans slug : {', '.join(self.empty_slug)}")
        return "; ".join(parts)


def get_or_create_legacy_index_page() -> tuple[ProduitIndexPage, bool]:
    """Return the /dechet index page, creating it under the live HomePage
    if needed. Returns (index_page, created)."""
    index_page = ProduitIndexPage.objects.filter(slug=LEGACY_PRODUIT_INDEX_SLUG).first()
    if index_page is not None:
        return index_page, False

    home = HomePage.objects.filter(live=True).first()
    if home is None:
        raise MigrationError(
            "Aucune HomePage publiée : impossible de créer l'index "
            f"'{LEGACY_PRODUIT_INDEX_SLUG}'."
        )
    index_page = ProduitIndexPage(
        title="Déchets",
        slug=LEGACY_PRODUIT_INDEX_SLUG,
    )
    home.add_child(instance=index_page)
    index_page.save_revision().publish()
    return index_page, True


def unique_slug(index_page: ProduitIndexPage, base_slug: str) -> str:
    """Return base_slug, suffixed with -2, -3, etc. if a sibling already
    uses it."""
    siblings = index_page.get_children()
    slug = base_slug
    counter = 2
    while siblings.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def migrate_produit(
    produit: Produit, index_page: ProduitIndexPage | None = None
) -> MigrationReport:
    """Migrate a single legacy Produit to a ProduitPage.

    Copies the legacy fields (prefixed ``legacy_``), creates the page under
    the /dechet index, imports the remaining synonymes as SearchTags
    (``legacy_imported_as_search_tag``) and records the migration on
    ``Produit.legacy_imported_as_produit_page``.

    Should be called inside a transaction; raises MigrationError when the
    produit is not eligible or the page cannot be created.
    """
    # Local import: qfdmd.views imports qfdmd.models, avoid an import cycle.
    from qfdmd.views import _execute_import

    if produit.legacy_imported_as_produit_page_id is not None:
        raise MigrationError("Ce produit a déjà été migré automatiquement.")
    if not Produit.objects.to_migrate().filter(pk=produit.pk).exists():
        raise MigrationError(
            "Ce produit est déjà redirigé manuellement vers une page Wagtail."
        )

    if index_page is None:
        index_page, _ = get_or_create_legacy_index_page()

    base_slug = slugify(produit.slug or produit.nom)
    if not base_slug:
        raise MigrationError("slug et nom vides, page impossible à créer.")

    page = ProduitPage(
        title=produit.nom,
        slug=unique_slug(index_page, base_slug),
        automatically_migrated_from_legacy_produit=True,
    )
    for field_name in PRODUIT_LEGACY_COPIED_FIELDS:
        value = getattr(produit, field_name)
        if field_name == "infotri":
            value = produit.infotri.raw_data or []
        setattr(page, f"legacy_{field_name}", value)

    index_page.add_child(instance=page)
    page.save_revision().publish()

    produit.legacy_imported_as_produit_page = page
    produit.save(update_fields=["legacy_imported_as_produit_page"])

    sync_msgs = page.sync_from_legacy_produit()

    log(
        instance=produit,
        action="qfdmd.migrate_produit",
        data={"page_id": page.pk, "page_title": page.title},
    )

    synonymes = produit.synonymes.filter(
        imported_as_search_tag__isnull=True,
        legacy_imported_as_search_tag__isnull=True,
    ).order_by("id")
    failed, truncated, empty_slug = _execute_import(
        page, synonymes, tracking_field="legacy_imported_as_search_tag"
    )
    return MigrationReport(
        page=page,
        sync_msgs=sync_msgs,
        failed=failed,
        truncated=truncated,
        empty_slug=empty_slug,
    )


def _is_orphan_search_tag(tag) -> bool:
    """A SearchTag created by the automatic migration is orphan once
    nothing references it anymore: no manually imported synonyme, no other
    automatically imported synonyme, and no remaining link to a page."""
    return (
        not tag.imported_synonymes.exists()
        and not tag.legacy_imported_synonymes.exists()
        and not TaggedSearchTag.objects.filter(tag=tag).exists()
    )


def revert_produit_migration(produit: Produit) -> None:
    """Revert an automatic migration.

    Deletes the ProduitPage created by :func:`migrate_produit`, removes the
    SearchTags imported alongside it when nothing else uses them, and clears
    the tracking fields so the produit becomes eligible for migration again.

    Should be called inside a transaction; raises MigrationError when the
    produit was not migrated automatically.
    """
    page = produit.legacy_imported_as_produit_page
    if page is None:
        raise MigrationError("Ce produit n'a pas été migré automatiquement.")
    if not page.automatically_migrated_from_legacy_produit:
        raise MigrationError(
            "La page liée n'a pas été créée par la migration automatique, "
            "annulation refusée."
        )

    tags = []
    for synonyme in produit.synonymes.filter(
        legacy_imported_as_search_tag__isnull=False
    ):
        tags.append(synonyme.legacy_imported_as_search_tag)
        synonyme.legacy_imported_as_search_tag = None
        synonyme.save(update_fields=["legacy_imported_as_search_tag"])

    # Deleting the page cascades the TaggedSearchTag through rows and sets
    # produit.legacy_imported_as_produit_page to NULL (on_delete=SET_NULL).
    page_title = page.title
    page.delete()
    produit.refresh_from_db()

    for tag in tags:
        if _is_orphan_search_tag(tag):
            tag.delete()

    log(
        instance=produit,
        action="qfdmd.revert_migration",
        data={"page_title": page_title},
    )
