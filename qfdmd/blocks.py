from sites_faciles.content_manager.blocks import (
    STREAMFIELD_COMMON_BLOCKS as SITES_FACILES_BLOCKS,
)
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock


class ProductBlock(blocks.StructBlock):
    champ = blocks.ChoiceBlock(
        choices=[("Bon état", "bon_etat"), ("Mauvais état", "mauvais_etat")]
    )
    produit = SnippetChooserBlock("qfdmd.produit", label="produit")


class ConsigneBlock(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock(label="Texte libre")
    reusable = SnippetChooserBlock(
        "qfdmd.reusablecontent",
        label="Contenu réutilisable",
        template="blocks/reusable.html",
    )
    produit = ProductBlock()


STREAMFIELD_COMMON_BLOCKS = [
    (
        "reusable",
        SnippetChooserBlock(
            "qfdmd.reusablecontent",
            label="Contenu réutilisable",
            template="blocks/reusable.html",
        ),
    ),
    *SITES_FACILES_BLOCKS,
]
