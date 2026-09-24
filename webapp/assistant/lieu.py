"""Reading a lieu for its detail page.

These functions turn raw fields into displayable information. They live
outside the view because they describe the lieu, not the page.
"""

# Only the Bonus Réparation is shown in the MVP: spec #3295 explicitly leaves
# out ESS and Répar'Acteurs, while V1 showed them all.
BONUS_REPARATION_CODES = ("bonusrepar", "BonusRepar_ASL", "bonusrepar_ABJ_TH")

# Value of `lieu_prestation` worth pointing out: the other one, `SUR_PLACE`,
# is the common case and tells the user nothing.
HOME_SERVICE_PRESTATION = "SUR_PLACE_OU_A_DOMICILE"


def offers_bonus(lieu) -> bool:
    """True if the lieu carries one of the Bonus Réparation labels.

    Several codes coexist in the database depending on the eco-organisme:
    treating them as one label avoids showing two for the same scheme.
    """
    return any(label.code in BONUS_REPARATION_CODES for label in lieu.labels.all())


def practical_info_of(lieu) -> list[str]:
    """The details worth knowing before going, in order of importance.

    Returns sentences rather than flags: the layout stays in the template, but
    the wording depends on the field, and duplicating it in the template would
    be worse.
    """
    infos = []

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


def gestes_of(lieu) -> list[dict]:
    """The gestes the lieu offers, deduplicated and ordered.

    An acteur carries one proposition de service per action; several actions
    share a groupe. The mockup (30142:9581) shows geste labels, hence groupes:
    without deduplication, "Réparer" would show as many times as there are
    actions in the groupe.
    """
    from assistant.consignes import GESTES_ORDER

    groupes = {}
    for proposition in lieu.proposition_services.all():
        groupe = proposition.action.groupe_action if proposition.action else None
        if groupe and groupe.code not in groupes:
            groupes[groupe.code] = {
                "code": groupe.code,
                "libelle": groupe.libelle_court or groupe.libelle,
            }

    order = {code: rank for rank, code in enumerate(GESTES_ORDER)}
    return sorted(groupes.values(), key=lambda g: order.get(g["code"], len(order)))
