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
