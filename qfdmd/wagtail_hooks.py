from django.contrib.auth.models import Permission
from django.urls import path, reverse
from draftjs_exporter.dom import DOM
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineEntityElementHandler,
)
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


def icon_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.
    Converts the ICON entities into a span tag.
    """
    print(f"👭 {props=}")

    return DOM.create_element(
        "img",
        {
            "width": "auto",
            "height": "16px",
            "src": props["icon"],
        },
        props["children"],
    )


class IconEntityElementHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState.
    Converts the span tag into a ICON entity, with the right data.
    """

    mutability = "IMMUTABLE"

    def get_attribute_data(self, attrs):
        """
        Take the `icon` value from the `data-icon` HTML attribute.
        """
        return attrs


@hooks.register("register_rich_text_features")
def register_icon_feature(features):
    feature_name = "icon"
    type_ = "ICON"
    control = {
        "type": type_,
        "label": "♺",
        "description": "Insérer une icone",
    }

    features.default_features.append(feature_name)
    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.EntityFeature(
            control, js=["wagtail/emoji.js"], css={"all": ["wagtail/emoji.css"]}
        ),
    )
    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            # Note here that the conversion is more complicated than for blocks and inline styles.
            "from_database_format": {"img": IconEntityElementHandler(type_)},
            "to_database_format": {"entity_decorators": {type_: icon_entity_decorator}},
        },
    )
