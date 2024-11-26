from wagtail import blocks
from wagtail.blocks.struct_block import StructBlock


class CarteBlock(StructBlock):
    gestes = blocks.MultipleChoiceBlock(
        choices=[
            ("reparer", "Reparer"),
            ("donner", "Donner"),
            ("preter", "Prêter"),
            ("acheter", "Acheter"),
        ]
    )
