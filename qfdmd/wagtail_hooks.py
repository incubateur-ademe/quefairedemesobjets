from django.contrib import messages
from django.contrib.auth.models import Permission
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem

from qfdmd.models import ProduitPage
from qfdmd.views import (
    bonus_viewset,
    import_legacy_synonymes,
    legacy_migrate,
    pokemon_chooser_viewset,
)


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(codename__in=["can_see_beta_search"])


@hooks.register("register_admin_viewset")
def register_pokemon_chooser_viewset():
    return pokemon_chooser_viewset


@hooks.register("register_admin_viewset")
def register_search_term_viewset():
    return search_term_viewset


@hooks.register("register_admin_viewset")
def register_bonus_viewset():
    return bonus_viewset


WagtailBlockChooserWidget = pokemon_chooser_viewset.widget_class


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
        """Only show this button for ProduitPage instances."""
        page = context.get("page")
        return page and isinstance(page.specific, ProduitPage)


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
    ]


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
