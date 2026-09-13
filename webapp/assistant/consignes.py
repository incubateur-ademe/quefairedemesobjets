"""Consignes de tri par geste.

Contenu statique en attendant le champ dédié sur `ProduitPage` (#3284). Quand
il existera, `consignes_pour()` le lira et ce module disparaîtra sans qu'aucun
appelant ne change : c'est tout l'intérêt de la fonction pivot.

Pas de dérivation transitoire depuis les propositions de service des acteurs :
elle produirait des consignes plausibles mais fausses, et serait plus difficile
à déloger qu'un texte manifestement générique.
"""

from urllib.parse import urlencode

from django.urls import reverse

from qfdmo.models.action import GroupeAction

# Hiérarchie d'affichage imposée par #3295 : réparable, puis bon état, puis
# hors d'usage. Les codes sont ceux des GroupeAction en base, pas des libellés :
# « déposer » dans la spec correspond au groupe `trier`.
ORDRE_GESTES = (
    "reparer",
    "donner_echanger_rapporter",
    "vendre_acheter",
    "emprunter_preter_louer",
    "trier",
)

# L'état conditionne le badge affiché en tête de bloc.
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

# Seule la réparation ouvre droit au Bonus Réparation.
GESTE_AVEC_BONUS = "reparer"


def consignes_pour(produit_page, parcours=None) -> list[dict]:
    """Consignes de la fiche, dans l'ordre d'affichage de la spec.

    `produit_page` n'est pas encore lu : il le sera quand le champ CMS
    existera (#3284). Le paramètre est là pour que la signature n'ait pas à
    changer ce jour-là.

    `parcours` sert à construire le lien vers les solutions : l'objet et
    l'adresse doivent suivre l'usager d'un écran à l'autre.
    """
    groupes = {groupe.code: groupe for groupe in GroupeAction.objects.all()}
    base = parcours.en_parametres() if parcours else {}

    consignes = []
    for code in ORDRE_GESTES:
        groupe = groupes.get(code)
        if groupe is None:
            continue

        etat, libelle_etat = ETATS[code]
        badges = [{"condition": etat, "libelle": libelle_etat}]
        if code == GESTE_AVEC_BONUS:
            badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

        parametres = urlencode({**base, "geste": code})
        consignes.append(
            {
                "geste": code,
                "libelle": groupe.libelle_court or groupe.libelle,
                "consigne": CONSIGNES[code],
                "badges": badges,
                "url": f"{reverse('assistant:solutions')}?{parametres}",
            }
        )
    return consignes
