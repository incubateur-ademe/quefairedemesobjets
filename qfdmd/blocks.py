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


class WagtailBlockChoiceBlock(blocks.StaticBlock):
    # Deprecated, kept to prevent migrations failure
    pass


class Bonus(blocks.StaticBlock):
    # Deprecated, kept to prevent migrations failure
    pass


class CustomBlockMixin(CommonStreamBlock):
    """Mixin to add common custom blocks to any block class."""

    reusable = SnippetChooserBlock(
        "qfdmd.reusablecontent",
        label="Contenu réutilisable",
        template="ui/blocks/reusable.html",
    )
    carte_sur_mesure = SnippetChooserBlock(
        "qfdmo.CarteConfig",
        label="Carte sur mesure",
        template="ui/blocks/carte.html",
    )
    liens = blocks.ListBlock(
        SnippetChooserBlock("qfdmd.Lien", label="Lien"),
        label="Liste de liens",
        template="ui/blocks/liens.html",
    )


class ColumnBlock(CustomBlockMixin):
    card = sites_faciles_blocks.VerticalCardBlock(
        label=_("Vertical card"), group=_("DSFR components")
    )
    contact_card = sites_faciles_blocks.VerticalContactCardBlock(
        label=_("Contact card"), group=_("Extra components")
    )


class TabBlock(sites_faciles_blocks.TabBlock):
    content = ColumnBlock(label=_("Content"))


class TabsBlock(sites_faciles_blocks.TabsBlock):
    tabs = TabBlock(label=_("Tab"), minnum=1, max_num=15)


STREAMFIELD_COMMON_BLOCKS = [
    *SITES_FACILES_BLOCKS,
    (
        "reusable",
        SnippetChooserBlock(
            "qfdmd.reusablecontent",
            label="Contenu réutilisable",
            template="ui/blocks/reusable.html",
        ),
    ),
    (
        "carte_sur_mesure",
        SnippetChooserBlock(
            "qfdmo.CarteConfig",
            label="Carte sur mesure",
            template="ui/blocks/carte.html",
        ),
    ),
    (
        "liens",
        blocks.ListBlock(
            SnippetChooserBlock("qfdmd.Lien", label="Lien"),
            label="Liste de liens",
            template="ui/blocks/liens.html",
        ),
    ),
    ("tabs", TabsBlock(label=_("Tabs"), group=_("DSFR components"))),
]
