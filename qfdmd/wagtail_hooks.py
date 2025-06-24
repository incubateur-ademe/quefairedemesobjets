from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem

from qfdmd.models import ProduitPage
from qfdmd.views import legacy_migrate


class MigratePageMenuItem(ActionMenuItem):
    name = "migrate-legacy"
    label = "Migrer depuis les produits/synonymes"
    icon_name = "download"

    def get_url(self, context):
        page = context["page"]
        return reverse("legacy_migrate", args=[page.id])

    def is_shown(self, context):
        return isinstance(context.get("page"), ProduitPage)


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
