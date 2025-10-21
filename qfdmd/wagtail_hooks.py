from django.contrib.auth.models import Permission
from django.templatetags.static import static
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.rich_text.editors.draftail import features as draftail_features

from qfdmd.views import (
    bonus_viewset,
    legacy_migrate,
    pokemon_chooser_viewset,
    reusable_content_viewset,
)


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(codename__in=["can_see_beta_search"])


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
        planned so we do not show it in Wagtail Admin.
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


@hooks.register("insert_editor_js")
def editor_js():
    return f'<script src="{static("wagtail/emoji.js")}"></script>'


@hooks.register("insert_editor_css")
def editor_css():
    return f'<link rel="stylesheet" href="{static("wagtail/emoji.css")}">'


@hooks.register("register_rich_text_features")
def register_emoji_feature(features):
    feature_name = "emoji"
    type_ = "EMOJI"

    control = {
        "type": type_,
        "label": "😊",
        "description": "Insérer un emoji",
    }

    features.register_editor_plugin(
        "draftail", feature_name, draftail_features.EntityFeature(control)
    )

    features.default_features.append(feature_name)
