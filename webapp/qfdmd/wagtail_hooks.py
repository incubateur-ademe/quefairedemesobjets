from django.contrib import messages
from django.contrib.auth.models import Permission
from django.db import transaction
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.log_actions import LogFormatter
from wagtail.snippets.action_menu import ActionMenuItem as SnippetActionMenuItem
from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail.snippets.permissions import get_permission_name

from qfdmd.legacy_migration import (
    MigrationError,
    get_or_create_legacy_index_page,
    migrate_produit,
    revert_produit_migration,
)
from qfdmd.models import Produit, ProduitPage
from qfdmd.views import (
    import_legacy_synonymes,
    legacy_migrate,
    migrate_single_produit,
    revert_single_produit,
    sync_page_from_produit,
    ProduitsViewSetGroup,
)


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(codename__in=["can_see_beta_search"])


class MigratePageMenuItem(ActionMenuItem):
    # TODOWAGTAIL: remove if not needed in a few weeks (2025/8/25)
    name = "migrate-legacy"
    label = "Migrer depuis les produits/synonymes"
    icon_name = "download"

    def get_url(self, context):
        page = context["page"]
        return reverse("legacy_migrate", args=[page.id])

    def is_shown(self, context):
        """
        We keep this class in case it needs to be enabled
        in a near future, but this can be considered as deprecated
        for now as a migration from produit / synonyme is no longer
        planned so we do not show it in Wagtail Admin.
        """
        return False


class ImportLegacySynonymesMenuItem(ActionMenuItem):
    name = "import-legacy-synonymes"
    label = "Importer les synonymes de recherche"
    icon_name = "download"

    def get_url(self, context):
        page = context["page"]
        return reverse("import_legacy_synonymes", args=[page.id])

    def is_shown(self, context):
        """Only show for ProduitPage instances that have not been migrated."""
        page = context.get("page")
        if not page:
            return False
        specific = page.specific if hasattr(page, "specific") else page
        return (
            isinstance(specific, ProduitPage)
            and not specific.migree_depuis_synonymes_legacy
        )


@hooks.register("register_page_action_menu_item")
def register_sync_page_menu_item():
    return MigratePageMenuItem(order=10)


@hooks.register("register_page_action_menu_item")
def register_import_legacy_synonymes_menu_item():
    return ImportLegacySynonymesMenuItem(order=11)


@hooks.register("register_admin_urls")
def register_legacy_migrate_url():
    return [
        path(
            "legacy/migrate/<str:id>/",
            legacy_migrate,
            name="legacy_migrate",
        ),
        path(
            "legacy/import-synonymes/<str:id>/",
            import_legacy_synonymes,
            name="import_legacy_synonymes",
        ),
        path(
            "legacy/migrate-produit/<str:id>/",
            migrate_single_produit,
            name="migrate_single_produit",
        ),
        path(
            "legacy/revert-produit/<str:id>/",
            revert_single_produit,
            name="revert_single_produit",
        ),
        path(
            "legacy/sync-produit/<str:id>/",
            sync_page_from_produit,
            name="sync_page_from_produit",
        ),
    ]


@hooks.register("register_admin_viewset")
def register_produitpage_viewset():
    return ProduitsViewSetGroup()


@hooks.register("after_edit_page")
def check_synonyme_redirection_conflicts(request, page):
    """Check for conflicts in legacy_synonyme redirections."""
    from qfdmd.models import Produit

    if not hasattr(page, "legacy_synonyme"):
        return

    for synonyme_relation in page.legacy_synonymes.all():
        # Check if the synonyme's produit is already redirected
        try:
            produit_page = synonyme_relation.synonyme.produit.next_wagtail_page
            if produit_page.page.id != page.id:
                messages.warning(
                    request,
                    f"Attention : le synonyme "
                    f"'{synonyme_relation.synonyme.nom}' sera redirigé "
                    f"vers cette page, mais son produit "
                    f"'{synonyme_relation.synonyme.produit.nom}' est "
                    f"déjà redirigé vers '{produit_page.page.title}'. "
                    f"La redirection du synonyme aura la priorité.",
                )
        except Produit.next_wagtail_page.RelatedObjectDoesNotExist:
            # If produit has no redirection, no conflict
            pass


class BaseProduitMigrationBulkAction(SnippetBulkAction):
    """Base for the bulk actions of the legacy Produit migration.

    Runs a callback per object in its own savepoint, collects the errors
    and reports them in the success message.
    """

    models = [Produit]

    def check_perm(self, snippet):
        if getattr(self, "can_change_items", None) is None:
            self.can_change_items = self.request.user.has_perm(
                get_permission_name("change", Produit)
            )
        return self.can_change_items

    @classmethod
    def execute_action(cls, objects, **kwargs):
        instance = kwargs["self"]
        instance.errors = []
        instance.results = []
        succeeded = 0
        for produit in objects:
            try:
                with transaction.atomic():
                    result = cls.apply(instance, produit)
            except MigrationError as exc:
                instance.errors.append(f"{produit.nom} : {exc}")
            else:
                succeeded += 1
                instance.results.append(result)
        return succeeded, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        parts = [
            f'<a href="{reverse("wagtailadmin_pages:edit", args=[r[0]])}">'
            f"{r[1]}</a>"
            for r in self.results
            if r is not None
        ]
        message = self.success_message_template % {"count": num_parent_objects}
        if parts:
            message += "<ul><li>" + "</li><li>".join(parts) + "</li></ul>"
        if self.errors:
            message += f" Ignoré(s) : {' ; '.join(self.errors)}"
        return mark_safe(message)


@hooks.register("register_bulk_action")
class MigrateProduitsBulkAction(BaseProduitMigrationBulkAction):
    display_name = "Migrer vers une page"
    aria_label = "Migrer les produits sélectionnés vers des ProduitPage"
    action_type = "migrate_to_produit_page"
    template_name = "qfdmd/bulk_actions/confirm_bulk_migrate.html"
    action_priority = 10
    success_message_template = "%(count)d produit(s) migré(s) vers des ProduitPage."

    def annotate_items(self, items):
        eligible_ids = set(
            Produit.objects.to_migrate()
            .filter(pk__in=[produit.pk for produit in items])
            .values_list("pk", flat=True)
        )
        for produit in items:
            produit.migration_eligible = produit.pk in eligible_ids
        return items

    @staticmethod
    def apply(instance, produit):
        if getattr(instance, "index_page", None) is None:
            instance.index_page, _ = get_or_create_legacy_index_page()
        report = migrate_produit(produit, index_page=instance.index_page)
        return report.page.pk, report.page.title


@hooks.register("register_bulk_action")
class RevertProduitsMigrationBulkAction(BaseProduitMigrationBulkAction):
    display_name = "Annuler la migration"
    aria_label = "Annuler la migration automatique des produits sélectionnés"
    action_type = "revert_produit_page_migration"
    template_name = "qfdmd/bulk_actions/confirm_bulk_revert.html"
    action_priority = 20
    classes = {"serious"}
    success_message_template = "Migration annulée pour %(count)d produit(s)."

    def annotate_items(self, items):
        for produit in items:
            produit.migration_eligible = (
                produit.legacy_imported_as_produit_page_id is not None
            )
        return items

    @staticmethod
    def apply(instance, produit):
        revert_produit_migration(produit)
        return None


# Snippet action menu items for the Produit edit view


class MigrateProduitSnippetMenuItem(SnippetActionMenuItem):
    label = "Migrer vers une ProduitPage"
    name = "migrate-legacy-produit"
    icon_name = "doc-full-inverse"
    classname = ""

    def is_shown(self, context):
        if context.get("view") != "edit":
            return False
        instance = context.get("instance")
        if instance is None:
            return False
        return (
            instance.legacy_imported_as_produit_page_id is None
            and not instance.next_wagtail_page_id
        )

    def get_url(self, parent_context):
        return reverse(
            "migrate_single_produit",
            args=[parent_context["instance"].pk],
        )


class RevertProduitSnippetMenuItem(SnippetActionMenuItem):
    label = "Annuler la migration"
    name = "revert-legacy-produit"
    icon_name = "undo"
    classname = "action-secondary"

    def is_shown(self, context):
        if context.get("view") != "edit":
            return False
        instance = context.get("instance")
        if instance is None:
            return False
        page = instance.legacy_imported_as_produit_page
        return page is not None and page.automatically_migrated_from_legacy_produit

    def get_url(self, parent_context):
        return reverse(
            "revert_single_produit",
            args=[parent_context["instance"].pk],
        )


class ViewProduitPageSnippetMenuItem(SnippetActionMenuItem):
    label = "Voir la ProduitPage"
    name = "view-linked-produit-page"
    icon_name = "link"

    def is_shown(self, context):
        if context.get("view") != "edit":
            return False
        instance = context.get("instance")
        if instance is None:
            return False
        return instance.legacy_imported_as_produit_page_id is not None

    def get_url(self, parent_context):
        page = parent_context["instance"].legacy_imported_as_produit_page
        return reverse("wagtailadmin_pages:edit", args=[page.pk])


@hooks.register("register_snippet_action_menu_item")
def register_produit_migrate_snippet_menu_item(model):
    if model != Produit:
        return None
    return MigrateProduitSnippetMenuItem(order=90)


@hooks.register("register_snippet_action_menu_item")
def register_produit_revert_snippet_menu_item(model):
    if model != Produit:
        return None
    return RevertProduitSnippetMenuItem(order=91)


@hooks.register("register_snippet_action_menu_item")
def register_produit_view_page_snippet_menu_item(model):
    if model != Produit:
        return None
    return ViewProduitPageSnippetMenuItem(order=92)


# Page action menu items for the ProduitPage edit view


class ViewRelatedProduitPageMenuItem(ActionMenuItem):
    name = "view-related-produit"
    label = "Voir le produit legacy"
    icon_name = "link"

    def get_url(self, context):
        page = context["page"]
        produits = page.specific.legacy_imported_produits.values_list("pk", flat=True)
        if not produits:
            return None
        return reverse(
            "wagtailsnippets_qfdmd_produit:edit",
            args=[produits[0]],
        )

    def is_shown(self, context):
        page = context.get("page")
        if not page:
            return False
        return (
            page.specific_class is ProduitPage
            and page.specific.legacy_imported_produits.exists()
        )


class RevertPageMigrationMenuItem(ActionMenuItem):
    name = "revert-page-migration"
    label = "Annuler la migration"
    icon_name = "undo"

    def get_url(self, context):
        page = context["page"]
        produits = page.specific.legacy_imported_produits.values_list("pk", flat=True)
        if not produits:
            return None
        return reverse("revert_single_produit", args=[produits[0]])

    def is_shown(self, context):
        page = context.get("page")
        if not page:
            return False
        return (
            page.specific_class is ProduitPage
            and page.specific.automatically_migrated_from_legacy_produit
        )


@hooks.register("register_page_action_menu_item")
def register_produitpage_migration_menu_items():
    return RevertPageMigrationMenuItem(order=50)


@hooks.register("register_page_action_menu_item")
def register_produitpage_view_produit_menu_item():
    return ViewRelatedProduitPageMenuItem(order=51)


class SyncFromLegacyMenuItem(ActionMenuItem):
    name = "sync-from-legacy-produit"
    label = "Synchroniser depuis le produit legacy"
    icon_name = "reset"

    def get_url(self, context):
        page = context["page"]
        return reverse("sync_page_from_produit", args=[page.id])

    def is_shown(self, context):
        page = context.get("page")
        if not page:
            return False
        return (
            page.specific_class is ProduitPage
            and page.specific.linked_legacy_produit is not None
        )


@hooks.register("register_page_action_menu_item")
def register_sync_from_legacy_menu_item():
    return SyncFromLegacyMenuItem(order=52)


@hooks.register("register_log_actions")
def register_migration_log_actions(actions):
    @actions.register_action("qfdmd.migrate_produit")
    class MigrateProduitAction(LogFormatter):
        label = "Migration produit legacy"
        message = "Produit legacy migré automatiquement vers une ProduitPage"

    @actions.register_action("qfdmd.revert_migration")
    class RevertMigrationAction(LogFormatter):
        label = "Annulation migration"
        message = "Migration automatique annulée"

    @actions.register_action("qfdmd.sync_produit")
    class SyncProduitAction(LogFormatter):
        label = "Synchronisation contenu legacy"
        message = "Contenu synchronisé depuis le produit legacy"
