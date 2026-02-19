"""Comments in the file below are in French as it is aimed at product team
as well as technical team.

🇫🇷 Le fichier ci-dessous est commenté en francais car destiné en partie
aux équipes produits.
Tout ce qui n'est pas sous ASSISTANT est commun à la carte et à l'assistant.
"""

bonus_reparation = "Propose le Bonus Réparation"
DIGITAL_ACTEUR_CODE = "acteur_digital"
DEFAULT_MAP_CONTAINER_ID = "carte"

SHARE_BODY = ()

CARTE = {
    "partage": {
        "titre": "{NOM} : L’ADEME partage ses bonnes adresses",
        "corps": "J’ai trouvé une bonne adresse {NOM} grâce à l’ADEME : {URL}",
    },
    "ajouter_un_lieu": "Ajouter un lieu sur la carte",
    "ajouter_un_lieu_mode_liste": "Proposer un nouveau lieu",
    "nouvelle_recherche_dans_cette_zone": "Nouvelle recherche dans cette zone",
    "filtres_bouton": "Filtres",
}

MODE_LISTE = {"pagination_suffixe": "lieux du plus proche au plus loin"}

ACTEUR = {
    "plusieurs_labels": "Cet établissement dispose de plusieurs labels",
}

ASSISTANT = {
    "partage": {
        # Introduction utilisé lors du partage d'un acteur ou d'un produit / déchet
        "titre": "Découvrez le site de l'ADEME “Que faire de mes objets & déchets”",
        # Texte utilisé lors du partage d'un acteur ou d'un produit / déchet.
        # sert essentiellement pour le partage par email
        "corps": "Bonjour,\n "
        "Vous souhaitez encourager au tri et la consommation responsable, "
        "le site de l’ADEME Que faire de mes objets & déchets accompagne "
        "les citoyens grâce à des bonnes pratiques et adresses près de chez eux,"
        " pour éviter l'achat neuf et réduire les déchets.\n"
        "Découvrez le ici : {URL}",
    },
    "seo": {
        # Utilisé comme balise <title> dans les pages d'accueil et produit
        "title": "Que Faire de mes objets & déchets : votre assistant au tri",
        # Utilisé comme meta-description en l'absence de meta
        # description définie sur le produit
        "description": "Ne jetez pas vos objets ! Découvrez des adresses "
        "pour les donner, les réparer ou les remplacer.",
    },
    "infotri": {
        "lien": "https://www.ecologie.gouv.fr/info-tri",
        "texte_du_lien": "En savoir plus sur l’Info-tri",
    },
    "nouvelle_recherche": "Nouvelle recherche",
    "faites_decouvrir_ce_site": "Faites découvrir ce site !",
}

MAP_CONTAINER_ID = "map_container_id"
