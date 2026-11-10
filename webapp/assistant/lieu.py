"""What the lieu page shows, from the lieu's raw fields."""

from typing import TypedDict

from assistant.consignes import GESTES_ORDER
from qfdmo.models.acteur import DisplayedActeur

# The label codes of the Bonus Réparation, one per eco-organisme.
BONUS_REPARATION_CODES = ("bonusrepar", "BonusRepar_ASL", "bonusrepar_ABJ_TH")

HOME_SERVICE_PRESTATION = "SUR_PLACE_OU_A_DOMICILE"


class Geste(TypedDict):
    code: str
    libelle: str


#### Assistant V2 : fiche d'un lieu et géolocalisation - #3577⁠
# FIXME : pourquoi ne pas utiliser le champ bonus de LabelQualité
# et pouurquoi ce n'est pas la même liste ?
# en base on a la liste : bonusrepar, BonusRepar_ASL, bonusrepar_ABJ_TH
#                         ecomaison, refashion, qualirepar
def offers_bonus(lieu: DisplayedActeur) -> bool:
    return any(label.code in BONUS_REPARATION_CODES for label in lieu.labels.all())


def practical_info_of(lieu: DisplayedActeur) -> list[str]:
    """The details worth knowing before going, as sentences, most important
    first."""
    infos = []

    #### Assistant V2 : fiche d'un lieu et géolocalisation - #3577⁠
    # FIXME : On a beaucoup de texte répartit dans les fichiers, est-ce qu'on a pas intérêt
    # à ce,traliser tous les textes de l'assistant v2 dans un même fichier ?
    if lieu.lieu_prestation == HOME_SERVICE_PRESTATION:
        infos.append("Sur place ou à domicile")
    if lieu.uniquement_sur_rdv:
        infos.append("Uniquement sur rendez-vous")
    if lieu.exclusivite_de_reprisereparation:
        infos.append("Reprend uniquement les produits de ses propres marques")
    if lieu.reprise:
        infos.append(f"Reprise : {lieu.reprise}")
    if lieu.public_accueilli:
        infos.append(f"Public accueilli : {lieu.public_accueilli}")
    if lieu.consignes_dacces:
        infos.append(lieu.consignes_dacces)

    return infos


def gestes_of(lieu: DisplayedActeur, sous_categorie_ids=()) -> list[Geste]:
    """The gestes (GroupeAction) the lieu offers, once each, in display order.

    With the fiche's sous-catégories, only the gestes offered for that objet;
    every geste when none matches, rather than none.
    """
    propositions = list(lieu.proposition_services.all())
    if sous_categorie_ids:
        wanted = set(sous_categorie_ids)
        for_the_objet = [
            proposition
            for proposition in propositions
            if wanted.intersection(s.id for s in proposition.sous_categories.all())
        ]
        propositions = for_the_objet or propositions

    groupes = {}
    for proposition in propositions:
        groupe = proposition.action.groupe_action if proposition.action else None
        if groupe and groupe.code not in groupes:
            groupes[groupe.code] = {
                "code": groupe.code,
                "libelle": groupe.libelle_court or groupe.libelle,
            }

    order = {code: rank for rank, code in enumerate(GESTES_ORDER)}
    return sorted(groupes.values(), key=lambda g: order.get(g["code"], len(order)))
