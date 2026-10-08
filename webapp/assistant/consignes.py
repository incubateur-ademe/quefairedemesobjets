"""Sorting consignes per geste.

Read from the fiche's grid of consignes (#3284) when it has one. Until the
existing pages are migrated to that block, a fiche without grid still shows
the static text below, so the assistant never renders an empty fiche.
"""

from urllib.parse import urlencode

from django.urls import reverse

from qfdmd.blocks import ETAT_CHOICES
from qfdmo.models.action import Action, GroupeAction

# TODO: the counter on the buttons is out of the MVP (ADR 0010, #3295), and its
# 20 km count does not match the 20 markers of the map. Set back to True once
# product and design agree on what the number means.
COUNTER_ENABLED = False

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

    `parcours` builds the link to the solutions: the objet and the address
    must follow the user from one screen to the next. A block spanning several
    gestes repeats `geste` in the query string.

    A block is skipped when none of its gestes exists in the database.
    """
    base = parcours.as_params() if parcours else {}
    # The slug spares the solutions screen a label lookup, and the counter
    # needs it to narrow the places to the objet.
    if produit_page is not None and getattr(produit_page, "slug", None):
        base = {**base, "fiche": produit_page.slug}
    localise = bool(parcours and parcours.is_located)

    cms = produit_page.consignes if produit_page is not None else []
    if cms:
        return [
            block
            for block in (_from_cms(child, base, localise) for child in cms)
            if block
        ]

    known = set(GroupeAction.objects.values_list("code", flat=True))
    return [
        block
        for block in (_from_static(static, known, base, localise) for static in BLOCKS)
        if block
    ]


def _links(gestes, base, localise) -> dict:
    params = urlencode({**base, "geste": gestes}, doseq=True)
    return {
        "url": f"{reverse('assistant:solutions')}?{params}",
        # Without a position, the button offers geolocation instead. Decided
        # here, not from `url_compte`: the counter can be off with a position.
        "localise": localise,
        # Fetched after the page renders, only when there is a position.
        "url_compte": (
            f"{reverse('api_v1:lieux-compte')}?{params}"
            if COUNTER_ENABLED and localise
            else ""
        ),
    }


def _from_static(block, known, base, localise) -> dict | None:
    gestes = [code for code in block["gestes"] if code in known]
    if not gestes:
        return None

    etat, etat_label = block["etat"]
    badges = [{"condition": etat, "libelle": etat_label}]
    if block["bonus"]:
        badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

    return {
        "code": block["code"],
        "gestes": gestes,
        "libelle": block["libelle"],
        "consigne": block["consigne"],
        "badges": badges,
        **_links(gestes, base, localise),
    }


def _from_cms(child, base, localise) -> dict | None:
    """A consigne of the CMS block, in the shape of the static ones.

    The block stores Action codes (the open data vocabulary); the solutions
    screen wants GroupeAction codes, once each, in the order of the actions.
    """
    value = child.value
    gestes = list(dict.fromkeys(_groupes_of(value["gestes"])))
    if not gestes:
        return None

    badges = []
    if value["etat"]:
        badges.append(
            {"condition": value["etat"], "libelle": dict(ETAT_CHOICES)[value["etat"]]}
        )
    if value["lieu_de_depot"]:
        badges.append(
            {"condition": "lieu_de_depot", "libelle": value["lieu_de_depot"].libelle}
        )
    if value["bonus_reparation"]:
        badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

    return {
        "code": child.id,
        "gestes": gestes,
        "libelle": value["titre"],
        # RichText: rendered as HTML by the template, never escaped.
        "consigne": value["contenu"],
        "badges": badges,
        **_links(gestes, base, localise),
    }


# Out of the MVP: no consigne explains prêter / louer yet. Filtered when the
# fiche is read too, since a grid edited in the CMS may still list them.
EXCLUDED_GROUPES = {"emprunter_preter_louer"}


def _groupes_of(action_codes) -> list[str]:
    # ponytail: one query per consigne, a fiche holds a handful of them.
    groupes = dict(
        Action.objects.filter(code__in=action_codes, groupe_action__isnull=False)
        .exclude(groupe_action__code__in=EXCLUDED_GROUPES)
        .values_list("code", "groupe_action__code")
    )
    return [groupes[code] for code in action_codes if code in groupes]
