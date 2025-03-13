"""Comments in the file below are in French as it is aimed at product team
as well as technical team.

🇫🇷 Le fichier ci-dessous est commenté en francais car destiné en partie
aux équipes produits.
Tout ce qui n'est pas sous ASSISTANT est commun à la carte et à l'assistant.
"""

bonus_reparation = "Propose le Bonus Réparation"
DIGITAL_ACTEUR_CODE = "acteur_digital"

# Introduction utilisé lors du partage d'un acteur ou d'un produit / déchet
SHARE_INTRO = "Découvrez le site de l'ADEME “Que faire de mes objets & déchets”"
# Texte utilisé lors du partage d'un acteur ou d'un produit / déchet.
# sert essentiellement pour le partage par email
SHARE_BODY = (
    "Bonjour,\n "
    "Vous souhaitez encourager au tri et la consommation responsable, "
    "le site de l’ADEME Que faire de mes objets & déchets accompagne "
    "les citoyens grâce à des bonnes pratiques et adresses près de chez eux,"
    " pour éviter l'achat neuf et réduire les déchets.\n"
    "Découvrez le ici : "
)

ASSISTANT = {
    "seo": {
        # Utilisé comme balise <title> dans les pages d'accueil et produit
        "title": "Que Faire de mes déchets & objets : votre assistant au tri "
        "et à la consommation responsable",
        # Utilisé comme meta-description en l'absence de meta
        # description définie sur le produit
        "description": "Ne jetez pas vos objets ! Découvrez des adresses "
        "pour les donner, les réparer ou les remplacer.",
    }
}
