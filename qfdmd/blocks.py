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


class ProductBlock(blocks.StructBlock):
    champ = blocks.ChoiceBlock(
        choices=[("Bon état", "bon_etat"), ("Mauvais état", "mauvais_etat")]
    )
    produit = SnippetChooserBlock("qfdmd.produit", label="produit")


class ExtendedCommonStreamBlock(CommonStreamBlock):
    reusable = SnippetChooserBlock(
        "qfdmd.reusablecontent",
        label="Contenu réutilisable",
        template="blocks/reusable.html",
    )


class ColumnBlock(sites_faciles_blocks.ColumnBlock, ExtendedCommonStreamBlock):
    pass


class TabBlock(sites_faciles_blocks.TabBlock):
    content = ColumnBlock(label=_("Content"))


class TabsBlock(sites_faciles_blocks.TabsBlock):
    tabs = TabBlock(label=_("Tab"), min_num=1, max_num=15)


STREAMFIELD_COMMON_BLOCKS = [
    *SITES_FACILES_BLOCKS,
    (
        "reusable",
        SnippetChooserBlock(
            "qfdmd.reusablecontent",
            label="Contenu réutilisable",
            template="blocks/reusable.html",
        ),
    ),
    ("tabs", TabsBlock(label=_("Tabs"), group=_("DSFR components"))),
]
