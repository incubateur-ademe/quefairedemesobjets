"""Migration of legacy Produit snippets to ProduitPage, and revert.

Shared logic between the ``migrate_produits_legacy`` management command,
the bulk actions available on the Produit snippet listing and the
per-object admin views allowing to migrate / revert a single produit.
"""

from dataclasses import dataclass, field

from django.utils import timezone
from django.utils.text import slugify
from wagtail.log_actions import log

from qfdmd.models import (
    CATEGORIES_INDEX_SLUG,
    LEGACY_PRODUIT_INDEX_SLUG,
    PRODUIT_LEGACY_COPIED_FIELDS,
    HomePage,
    LegacyIntermediateProduitPage,
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

    main_synonyme = produit.synonymes.filter(nom=produit.nom).first()
    # Produit.slug is a single legacy field that can only hold one historic
    # URL, even though each synonyme had its own — it isn't reliably the
    # produit's own slug (e.g. it can be an unrelated synonyme's slug). The
    # main synonyme (same nom as the produit) carries the slug that actually
    # matches the produit and should be preferred for SEO continuity.
    base_slug = slugify(
        (main_synonyme.slug if main_synonyme else "") or produit.slug or produit.nom
    )
    if not base_slug:
        raise MigrationError("slug et nom vides, page impossible à créer.")

    page = ProduitPage(
        title=produit.nom,
        slug=unique_slug(index_page, base_slug),
        automatically_migrated_from_legacy_produit=True,
        # Locked for everyone (no locked_by) until the migration is
        # finalized, so nobody edits a page still driven by legacy data.
        locked=True,
        locked_at=timezone.now(),
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

    log_without_raising(
        produit,
        "qfdmd.migrate_produit",
        data={"page_id": page.pk, "page_title": page.title},
    )

    # The main synonyme (same nom as the produit) was used to build the
    # page itself: it must not also appear as one of the page's own
    # search synonymes.
    synonymes = (
        produit.synonymes.filter(
            imported_as_search_tag__isnull=True,
            legacy_imported_as_search_tag__isnull=True,
        )
        .exclude(nom=produit.nom)
        .order_by("id")
    )
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

    log_without_raising(
        produit, "qfdmd.revert_migration", data={"page_title": page_title}
    )


def finalize_produit_migration(page: ProduitPage) -> ProduitIndexPage:
    """Turn an automatically migrated page into a regular, hand-managed one.

    Moves the page under the /categories index, replaces the automatic
    links (``Produit.legacy_imported_as_produit_page``,
    ``Synonyme.legacy_imported_as_search_tag``) with the manual ones used
    by hand-migrated pages (``next_wagtail_page``,
    ``Synonyme.imported_as_search_tag``), clears the "migré
    automatiquement" flag and unlocks the page.

    Should be called inside a transaction; raises MigrationError when the
    page was not migrated automatically or the target index is missing.
    Returns the index page the page was moved under.
    """
    if not page.automatically_migrated_from_legacy_produit:
        raise MigrationError("Cette page n'a pas été migrée automatiquement.")
    categories = ProduitIndexPage.objects.filter(slug=CATEGORIES_INDEX_SLUG).first()
    if categories is None:
        raise MigrationError(
            f"Page index « {CATEGORIES_INDEX_SLUG} » introuvable, "
            "déplacement impossible."
        )

    produit = page.linked_legacy_produit
    if produit is not None:
        for synonyme in produit.synonymes.filter(
            legacy_imported_as_search_tag__isnull=False
        ):
            synonyme.imported_as_search_tag = synonyme.legacy_imported_as_search_tag
            synonyme.legacy_imported_as_search_tag = None
            synonyme.save(
                update_fields=[
                    "imported_as_search_tag",
                    "legacy_imported_as_search_tag",
                ]
            )
        produit.legacy_imported_as_produit_page = None
        produit.save(update_fields=["legacy_imported_as_produit_page"])
        LegacyIntermediateProduitPage.objects.get_or_create(
            produit=produit, defaults={"page": page}
        )

    page.automatically_migrated_from_legacy_produit = False
    page.locked = False
    page.locked_by = None
    page.locked_at = None
    if page.get_parent().pk != categories.pk:
        page.slug = unique_slug(categories, page.slug)
    page.save()
    if page.get_parent().pk != categories.pk:
        page.move(categories, pos="last-child")
        page.refresh_from_db()

    log_without_raising(
        page,
        "qfdmd.finalize_migration",
        data={"produit_id": produit.pk if produit else None},
    )
    return categories


def log_without_raising(instance, action, **kwargs):
    try:
        log(instance=instance, action=action, **kwargs)
    except Exception:
        pass
