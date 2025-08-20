import logging

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from sites_faciles.content_manager import blocks as sites_faciles_blocks
from sites_faciles.content_manager.blocks import (
    STREAMFIELD_COMMON_BLOCKS as SITES_FACILES_BLOCKS,
)
from sites_faciles.content_manager.blocks import (
    CommonStreamBlock,
)
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

logger = logging.getLogger(__name__)


class ProductBlock(blocks.StructBlock):
    champ = blocks.ChoiceBlock(
        choices=[("Bon état", "bon_etat"), ("Mauvais état", "mauvais_etat")],
    )
    produit = SnippetChooserBlock("qfdmd.produit", label="produit")


def get_choices(*args, **kwargs) -> list:
    logger.info(f"{args=} {kwargs=}")
    return [("coucou", "coucou")]


reusable_block = SnippetChooserBlock(
    "qfdmd.reusablecontent",
    label="Contenu réutilisable",
    template="blocks/reusable.html",
)

carte_sur_mesure_block = SnippetChooserBlock(
    "qfdmo.CarteConfig",
    label="Carte sur mesure",
    template="blocks/carte.html",
)


class ExtendedCommonStreamBlock(CommonStreamBlock):
    reusable = reusable_block
    carte_sur_mesure = carte_sur_mesure_block


class ColumnBlock(sites_faciles_blocks.ColumnBlock):
    reusable = reusable_block
    carte_sur_mesure = carte_sur_mesure_block


class TabBlock(sites_faciles_blocks.TabBlock):
    content = ColumnBlock(label=_("Content"))


class TabsBlock(sites_faciles_blocks.TabsBlock):
    tabs = TabBlock(label=_("Tab"), minnum=1, max_num=15)


class Bonus(blocks.StaticBlock):
    class Meta:
        template = "blocks/bonus.html"
        label = "Bonus réparation"


class WagtailBlockChoiceBlock(blocks.ChooserBlock):
    @cached_property
    def target_model(self):
        from qfdmd.views import WagtailBlock

        return WagtailBlock

    @cached_property
    def widget(self):
        from qfdmd.wagtail_hooks import WagtailBlockChooserWidget

        return WagtailBlockChooserWidget(
            linked_fields={"parent_page_id": "#id_parent_page_id"}
        )


class Override(blocks.StructBlock):
    block = WagtailBlockChoiceBlock()
    content = ExtendedCommonStreamBlock()


STREAMFIELD_COMMON_BLOCKS = [
    *SITES_FACILES_BLOCKS,
    ("override", Override()),
    ("bonus", Bonus()),
    (
        "reusable",
        reusable_block,
    ),
    (
        "carte_sur_mesure",
        carte_sur_mesure_block,
    ),
    ("tabs", TabsBlock(label=_("Tabs"), group=_("DSFR components"))),
]
