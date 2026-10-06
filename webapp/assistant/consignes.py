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

# The condition drives the badge shown at the top of the block.
ETATS = {
    "reparer": ("reparable", "Réparable"),
    "donner_echanger_rapporter": ("bon_etat", "Bon état"),
    "vendre_acheter": ("bon_etat", "Bon état"),
    "emprunter_preter_louer": ("bon_etat", "Bon état"),
    "trier": ("mauvais_etat", "Mauvais état"),
}

CONSIGNES = {
    "reparer": (
        "Votre objet est abîmé mais réparable ? La réparation prolonge sa durée"
        " de vie et coûte souvent moins cher qu'un remplacement. Les"
        " réparateurs proposant le Bonus Réparation sont signalés par le"
        " symbole %."
    ),
    "donner_echanger_rapporter": (
        "Votre objet fonctionne encore et peut servir à quelqu'un d'autre ?"
        " Le donner ou l'échanger lui offre une seconde vie, sans passer par"
        " la case déchet."
    ),
    "vendre_acheter": (
        "Votre objet est en bon état et a encore de la valeur ? Le revendre"
        " permet à quelqu'un d'en profiter, et à vous d'en tirer un revenu."
    ),
    "emprunter_preter_louer": (
        "Vous n'avez besoin de cet objet que ponctuellement ? Le prêt et la"
        " location évitent un achat, et l'objet sert à plusieurs personnes."
    ),
    "trier": (
        "Votre objet est hors d'usage ? Il ne se jette pas avec les ordures"
        " ménagères : déposez-le en point de collecte pour qu'il soit recyclé"
        " ou traité correctement."
    ),
}

# Only repair gives access to the Bonus Réparation.
GESTE_WITH_BONUS = "reparer"


def consignes_for(produit_page, parcours=None) -> list[dict]:
    """Consignes of the fiche, in the display order of the spec.

    `produit_page` is not read yet: it will be once the CMS field exists
    (#3284). The parameter is there so the signature does not change that day.

    `parcours` builds the link to the solutions: the objet and the address
    must follow the user from one screen to the next.
    """
    groupes = {groupe.code: groupe for groupe in GroupeAction.objects.all()}
    base = parcours.as_params() if parcours else {}

    consignes = []
    for code in GESTES_ORDER:
        groupe = groupes.get(code)
        if groupe is None:
            continue

        etat, etat_label = ETATS[code]
        badges = [{"condition": etat, "libelle": etat_label}]
        if code == GESTE_WITH_BONUS:
            badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

        params = urlencode({**base, "geste": code})
        consignes.append(
            {
                "geste": code,
                "libelle": groupe.libelle_court or groupe.libelle,
                "consigne": CONSIGNES[code],
                "badges": badges,
                "url": f"{reverse('assistant:solutions')}?{params}",
            }
        )
    return consignes
