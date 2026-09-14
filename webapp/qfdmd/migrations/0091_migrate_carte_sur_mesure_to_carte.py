from django.db import migrations
from wagtail.blocks.migrations.migrate_operation import MigrateStreamData
from wagtail.blocks.migrations.operations import BaseBlockOperation


class CarteSurMesureToCarteOperation(BaseBlockOperation):
    """Turn ``{"type": "carte_sur_mesure", "value": <id>}`` stream children into
    ``{"type": "carte", "value": {"carte_config": <id>}}``.

    ``open_in_modal`` and ``card`` are left unset so migrated pages keep their
    current inline rendering.
    """

    def apply(self, block_value):
        return [
            (
                {**child, "type": "carte", "value": {"carte_config": child["value"]}}
                if child["type"] == "carte_sur_mesure"
                else child
            )
            for child in block_value
        ]

    @property
    def operation_name_fragment(self):
        return "carte_sur_mesure_to_carte"


# Paths to every StreamBlock that could hold a ``carte_sur_mesure`` child:
# the page body itself and the content of each tab.
BLOCK_PATHS = ["", "tabs.tabs.content"]
MODELS = ["LegacyProduitIndexPage", "ProduitIndexPage", "ProduitPage"]


class Migration(migrations.Migration):
    dependencies = [("qfdmd", "0090_carte_block")]

    operations = [
        MigrateStreamData(
            app_name="qfdmd",
            model_name=model_name,
            field_name="body",
            operations_and_block_paths=[
                (CarteSurMesureToCarteOperation(), path) for path in BLOCK_PATHS
            ],
        )
        for model_name in MODELS
    ]
