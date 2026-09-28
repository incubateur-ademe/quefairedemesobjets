import logging

from django.utils.translation import gettext_lazy as _
from sites_conformes.content_manager import blocks as sites_conformes_blocks
from sites_conformes.content_manager.blocks import (
    STREAMFIELD_COMMON_BLOCKS as sites_conformes_BLOCKS,
)
from sites_conformes.content_manager.blocks import (
    CommonStreamBlock,
)
from sites_conformes.content_manager.constants import GRID_3_4_6_CHOICES
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

    Use this on pages that do **not** have a ``carte`` block.
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
            "Utilisez-le sur les fiches qui n'ont pas de « Carte »."
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


# The three conditions of an objet, badges of the fiche (Figma 24381:25) and
# values of the `etat` column in the consignes open data.
ETAT_CHOICES = [
    ("reparable", "Réparable"),
    ("bon_etat", "Bon état"),
    ("mauvais_etat", "Mauvais état"),
]


def action_choices():
    """Action codes, the vocabulary of the acteurs open data: a reuser joins
    a consigne to the places on `gestes` without a mapping table.

    Every action, whatever `afficher` says: that flag hides an action from
    the carte's filters, and `trier` is hidden there while being the geste
    of every déchet consigne.
    """
    from qfdmo.models.action import Action

    return list(Action.objects.order_by("order").values_list("code", "libelle"))


class ConsigneBlock(blocks.StructBlock):
    """One consigne: what to do with the objet or déchet for given gestes.

    Typed fields rather than free badges so the content can be exported as
    open data and read by the assistant (#3284).
    """

    titre = blocks.CharBlock(label="Titre")
    contenu = blocks.RichTextBlock(
        label="Contenu", features=["bold", "link", "ol", "ul"]
    )
    lien = blocks.PageChooserBlock(label="Lien vers une page du site", required=False)
    gestes = blocks.MultipleChoiceBlock(
        label="Gestes",
        choices=action_choices,
        help_text="Les gestes que cette consigne décrit (donner, revendre…)",
    )
    etat = blocks.ChoiceBlock(
        label="État",
        choices=ETAT_CHOICES,
        required=False,
        help_text="Objets uniquement",
    )
    lieu_de_depot = SnippetChooserBlock(
        "qfdmd.LieuDeDepot",
        label="Lieu de dépôt",
        required=False,
        help_text="Déchets uniquement",
    )
    bonus_reparation = blocks.BooleanBlock(
        label="Éligible au bonus réparation", required=False
    )

    class Meta:
        template = "ui/blocks/consigne.html"
        icon = "list-ul"
        label = "Consigne"


class ConsignesBlock(blocks.StructBlock):
    """A grid of consignes: the item grid of Sites conformes, with typed
    cards. A page may hold several, for instance one per lieu de dépôt.
    The column widths are those of the item grid, so a migrated row keeps
    its layout."""

    column_width = blocks.ChoiceBlock(
        label="Largeur de colonne",
        choices=[*GRID_3_4_6_CHOICES, ("12", "12/12")],
        default="4",
    )
    consignes = blocks.ListBlock(ConsigneBlock(), label="Consignes", max_num=4)

    class Meta:
        template = "ui/blocks/consignes.html"
        icon = "grip"
        label = "Grille de consignes"
        group = "3. Page structure"


class CustomBlockMixin(CommonStreamBlock):
    """Mixin to add common custom blocks to any block class."""

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
    ("break", BreakBlock()),
    ("carte", CarteBlock(label="Carte")),
    ("consignes", ConsignesBlock()),
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
