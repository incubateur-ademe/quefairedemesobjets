from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem

from qfdmd.views import (
    bonus_viewset,
    legacy_migrate,
    pokemon_chooser_viewset,
    reusable_content_viewset,
)


@hooks.register("register_admin_viewset")
def register_pokemon_chooser_viewset():
    return pokemon_chooser_viewset


@hooks.register("register_admin_viewset")
def register_reusable_viewset():
    return reusable_content_viewset


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
        planned
        """
        return False


@hooks.register("register_page_action_menu_item")
def register_sync_page_menu_item():
    return MigratePageMenuItem(order=10)


@hooks.register("register_admin_urls")
def register_legacy_migrate_url():
    return [
        path(
            "legacy/migrate/<str:id>/",
            legacy_migrate,
            name="legacy_migrate",
        ),
    ]
