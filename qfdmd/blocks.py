from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock


class ConsigneBlock(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock(label="Texte libre")
    reusable = SnippetChooserBlock(
        "qfdmd.reusablecontent",
        label="Contenu réutilisable",
        template="blocks/reusable.html",
    )
