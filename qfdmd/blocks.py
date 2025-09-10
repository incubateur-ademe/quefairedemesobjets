import logging

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


COMMON_CUSTOM_BLOCKS = {
    "reusable": SnippetChooserBlock(
        "qfdmd.reusablecontent",
        label="Contenu réutilisable",
        template="blocks/reusable.html",
    ),
    "carte_sur_mesure": SnippetChooserBlock(
        "qfdmo.CarteConfig",
        label="Carte sur mesure",
        template="blocks/carte.html",
    ),
    "liens": blocks.ListBlock(
        SnippetChooserBlock("qfdmd.Lien", label="Lien"),
        label="Liste de liens",
        template="blocks/liens.html",
    ),
}


class WagtailBlockChoiceBlock(blocks.StaticBlock):
    # Deprecated, kept to prevent migrations failure
    pass


class CustomBlockMixin:
    """Mixin to add common custom blocks to any block class."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, block in COMMON_CUSTOM_BLOCKS.items():
            setattr(cls, name, block)


class ExtendedCommonStreamBlock(CustomBlockMixin, CommonStreamBlock):
    pass


class ColumnBlock(CustomBlockMixin, sites_faciles_blocks.ColumnBlock):
    pass


class TabBlock(sites_faciles_blocks.TabBlock):
    content = ColumnBlock(label=_("Content"))


class TabsBlock(sites_faciles_blocks.TabsBlock):
    tabs = TabBlock(label=_("Tab"), minnum=1, max_num=15)


class Bonus(blocks.StaticBlock):
    class Meta:
        template = "blocks/bonus.html"
        label = "Bonus réparation"


STREAMFIELD_COMMON_BLOCKS = [
    *SITES_FACILES_BLOCKS,
    ("bonus", Bonus()),
    ("reusable", COMMON_CUSTOM_BLOCKS["reusable"]),
    ("carte_sur_mesure", COMMON_CUSTOM_BLOCKS["carte_sur_mesure"]),
    ("liens", COMMON_CUSTOM_BLOCKS["liens"]),
    ("tabs", TabsBlock(label=_("Tabs"), group=_("DSFR components"))),
]
