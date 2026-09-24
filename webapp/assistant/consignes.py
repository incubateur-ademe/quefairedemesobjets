"""Sorting consignes per geste.

Static content until the dedicated field on `ProduitPage` exists (#3284). When
it does, `consignes_for()` will read it and this module will disappear without
any caller changing: that is the point of the pivot function.

No transitional derivation from the acteurs' propositions de service: it would
produce plausible but wrong consignes, harder to dislodge than an obviously
generic text.
"""

from urllib.parse import urlencode

from django.urls import reverse

from qfdmo.models.action import GroupeAction

# Display hierarchy imposed by #3295: repairable, then good condition, then
# out of use. The codes are those of the GroupeAction in the database, not
# labels: "déposer" in the spec corresponds to the `trier` groupe.
GESTES_ORDER = (
    "reparer",
    "donner_echanger_rapporter",
    "vendre_acheter",
    "emprunter_preter_louer",
    "trier",
)

# The three blocks of the fiche (Figma 30139:14476): one per condition of the
# objet, each carrying the gestes that apply. "Donner ou revendre" spans two
# GroupeAction, hence a list; its label exists nowhere in the database.
# `emprunter_preter_louer` is not on the mockup and stays out.
BLOCKS = (
    {
        "code": "reparer",
        "gestes": ("reparer",),
        "libelle": "Réparer",
        "etat": ("reparable", "Réparable"),
        "bonus": True,
        "consigne": (
            "Votre objet est abîmé mais réparable ? La réparation prolonge sa"
            " durée de vie et coûte souvent moins cher qu'un remplacement. Les"
            " réparateurs proposant le Bonus Réparation sont signalés par le"
            " symbole %."
        ),
    },
    {
        "code": "donner_revendre",
        "gestes": ("donner_echanger_rapporter", "vendre_acheter"),
        "libelle": "Donner ou revendre",
        "etat": ("bon_etat", "Bon état"),
        "bonus": False,
        "consigne": (
            "Votre objet fonctionne encore et peut servir à quelqu'un d'autre ?"
            " Proposez-le à un proche, donnez-le à une association ou à une"
            " structure de réemploi. Vous pouvez aussi essayer de le revendre"
            " sur une plateforme de seconde main ou en dépôt-vente."
        ),
    },
    {
        "code": "trier",
        "gestes": ("trier",),
        "libelle": "Déposer",
        "etat": ("mauvais_etat", "Mauvais état"),
        "bonus": False,
        "consigne": (
            "Votre objet est hors d'usage ? Il ne se jette pas avec les ordures"
            " ménagères : déposez-le en point de collecte pour qu'il soit recyclé"
            " ou traité correctement."
        ),
    },
)


def block_for(gestes) -> dict | None:
    """The block whose gestes are exactly these, whatever their order."""
    wanted = frozenset(gestes)
    return next(
        (block for block in BLOCKS if frozenset(block["gestes"]) == wanted), None
    )


def consignes_for(produit_page, parcours=None) -> list[dict]:
    """Blocks of the fiche, in the display order of the spec.

    `produit_page` is not read yet: it will be once the CMS field exists
    (#3284). The parameter is there so the signature does not change that day.

    `parcours` builds the link to the solutions: the objet and the address
    must follow the user from one screen to the next. A block spanning several
    gestes repeats `geste` in the query string.

    A block is skipped when none of its gestes exists in the database.
    """
    known = set(GroupeAction.objects.values_list("code", flat=True))
    base = parcours.as_params() if parcours else {}

    consignes = []
    for block in BLOCKS:
        gestes = [code for code in block["gestes"] if code in known]
        if not gestes:
            continue

        etat, etat_label = block["etat"]
        badges = [{"condition": etat, "libelle": etat_label}]
        if block["bonus"]:
            badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

        params = urlencode({**base, "geste": gestes}, doseq=True)
        consignes.append(
            {
                "code": block["code"],
                "gestes": gestes,
                "libelle": block["libelle"],
                "consigne": block["consigne"],
                "badges": badges,
                "url": f"{reverse('assistant:solutions')}?{params}",
            }
        )
    return consignes
