"""Lecture d'un lieu pour sa fiche détaillée.

Ces fonctions traduisent des champs bruts en informations affichables. Elles
vivent hors de la vue parce qu'elles décrivent le lieu, pas la page.
"""

# Seul le Bonus Réparation est affiché dans le MVP : la spec #3295 écarte
# explicitement ESS et Répar'Acteurs, alors que la V1 les montrait tous.
CODES_BONUS_REPARATION = ("bonusrepar", "BonusRepar_ASL", "bonusrepar_ABJ_TH")

# Valeur du champ `lieu_prestation` qui mérite d'être signalée : l'autre,
# `SUR_PLACE`, est le cas courant et n'apprend rien à l'usager.
PRESTATION_A_DOMICILE = "SUR_PLACE_OU_A_DOMICILE"


def propose_le_bonus(lieu) -> bool:
    """Vrai si le lieu porte l'un des labels du Bonus Réparation.

    Plusieurs codes coexistent en base selon l'éco-organisme : les traiter
    comme un seul label évite d'en afficher deux pour le même dispositif.
    """
    return any(label.code in CODES_BONUS_REPARATION for label in lieu.labels.all())


def infos_pratiques_de(lieu) -> list[str]:
    """Les précisions utiles avant de se déplacer, dans l'ordre d'importance.

    Renvoie des phrases plutôt que des drapeaux : la mise en forme reste au
    gabarit, mais la formulation dépend du champ, et la dupliquer en template
    serait pire.
    """
    infos = []

    if lieu.lieu_prestation == PRESTATION_A_DOMICILE:
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


def gestes_de(lieu) -> list[dict]:
    """Les gestes que le lieu propose, dédupliqués et ordonnés.

    Un acteur porte une proposition de service par action ; plusieurs actions
    partagent un même groupe. La maquette (30142:9581) montre des étiquettes de
    geste, donc des groupes : sans déduplication, « Réparer » s'afficherait
    autant de fois qu'il y a d'actions dans le groupe.
    """
    from assistant.consignes import ORDRE_GESTES

    groupes = {}
    for proposition in lieu.proposition_services.all():
        groupe = proposition.action.groupe_action if proposition.action else None
        if groupe and groupe.code not in groupes:
            groupes[groupe.code] = {
                "code": groupe.code,
                "libelle": groupe.libelle_court or groupe.libelle,
            }

    ordre = {code: rang for rang, code in enumerate(ORDRE_GESTES)}
    return sorted(groupes.values(), key=lambda g: ordre.get(g["code"], len(ordre)))
