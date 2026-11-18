"""Raw StreamField content for the consignes tests."""

import json

from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory


def consigne(titre, block_id="00000000-0000-0000-0000-000000000000", **extra):
    """A list item as the CMS stores it, id included."""
    return {
        "type": "item",
        "id": block_id,
        "value": {
            "titre": titre,
            "contenu": f"<p>{titre}</p>",
            "gestes": ["donner"],
            **extra,
        },
    }


def grid(*consignes, column_width="4"):
    return {
        "type": "consignes",
        "value": {"column_width": column_width, "consignes": list(consignes)},
    }


def paragraph(text):
    return {"type": "paragraph", "value": f"<p>{text}</p>"}


def page_with(*blocks, **kwargs):
    """Raw JSON, as read from the database: the values go through the
    blocks' normalisation, unlike Python values handed to the factory."""
    return ProduitPageFactory(body=json.dumps(list(blocks)), **kwargs)
