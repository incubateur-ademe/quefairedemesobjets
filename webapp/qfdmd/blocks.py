import logging

from django.utils.translation import gettext_lazy as _
from sites_conformes.content_manager import blocks as sites_conformes_blocks
from sites_conformes.content_manager.blocks import (
    STREAMFIELD_COMMON_BLOCKS as sites_conformes_BLOCKS,
)
from sites_conformes.content_manager.blocks import (
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


class BreakBlock(blocks.StaticBlock):
    """Invisible marker to split iframe vs standalone content.

    When placed in a ``ProduitPage`` body, everything after this block is
    hidden when the page is rendered inside an iframe. The block itself
    renders nothing — it is purely a layout boundary.

    Use this on pages that do **not** have a ``carte_sur_mesure`` block.
    The iframe cut-point logic picks whichever comes first: the carte block
    or this break block.
    """

    class Meta:
        icon = "horizontal-rule"
        label = "Césure iframe"
        group = "3. Page structure"
        admin_text = _(
            "Tout ce qui se trouve après ce bloc est masqué lorsque la page est "
            "affichée dans une iframe (par ex. intégration sur un site partenaire). "
            "Utilisez-le sur les fiches qui n'ont pas de « Carte sur mesure »."
        )
class CarteBlock(blocks.StructBlock):
    """StructBlock wrapping a CarteConfig snippet with a mobile display toggle."""

    carte_config = SnippetChooserBlock(
        "qfdmo.CarteConfig",
        label="Configuration de carte",
    )
    card = sites_conformes_blocks.VerticalCardBlock(
        label="Carte DSFR",
        help_text=(
            "Carte affichée en teaser sur mobile lorsque le mode modale est activé."
            " Ne pas définir de lien — le clic ouvre la modale."
        ),
        required=False,
    )
    open_in_modal = blocks.BooleanBlock(
        required=False,
        label="Afficher dans une modale",
        help_text=(
            "Sur mobile, la carte sera masquée derrière une carte DSFR cliquable"
        ),
    )

    class Meta:
        template = "ui/blocks/carte_block.html"
        label = "Carte"
        icon = "map"


class CustomBlockMixin(CommonStreamBlock):
    """Mixin to add common custom blocks to any block class."""

    carte_sur_mesure = SnippetChooserBlock(
        "qfdmo.CarteConfig",
        label="Carte sur mesure",
        template="ui/blocks/carte.html",
    )
    carte = CarteBlock(label="Carte")
    liens = blocks.ListBlock(
        SnippetChooserBlock("qfdmd.Lien", label="Lien"),
        label="Liste de liens",
        template="ui/blocks/liens.html",
    )


class ColumnBlock(CustomBlockMixin):
    card = sites_conformes_blocks.VerticalCardBlock(
        label=_("Vertical card"), group=_("DSFR components")
    )
    contact_card = sites_conformes_blocks.VerticalContactCardBlock(
        label=_("Contact card"), group=_("Extra components")
    )


class TabBlock(sites_conformes_blocks.TabBlock):
    content = ColumnBlock(label=_("Content"))


class TabsBlock(sites_conformes_blocks.TabsBlock):
    tabs = TabBlock(label=_("Tab"), minnum=1, max_num=15)


STREAMFIELD_COMMON_BLOCKS = [
    *sites_conformes_BLOCKS,
    (
        "carte_sur_mesure",
        SnippetChooserBlock(
            "qfdmo.CarteConfig",
            label="Carte sur mesure",
            template="ui/blocks/carte.html",
        ),
    ),
    ("break", BreakBlock()),
    (
        "carte",
        CarteBlock(label="Carte"),
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
