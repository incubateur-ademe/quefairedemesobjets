"""Constants for Info-tri feature."""

# Categorie choices
CATEGORIE_CHOICES = [
    ("tous", "Tous"),
    ("textile", "Textiles d'habillement"),
    ("vetement", "Linges de maison"),
    ("chaussures", "Chaussures"),
]

# Maps each categorie value to its SVG template path
CATEGORIE_SVG_TEMPLATES = {
    "tous": "ui/components/infotri/svg/tous.html",
    "textile": "ui/components/infotri/svg/textile.html",
    "vetement": "ui/components/infotri/svg/linge.html",
    "chaussures": "ui/components/infotri/svg/chaussures.html",
}

# Consigne choices
CONSIGNE_CHOICES = [
    ("1", "À déposer dans un conteneur"),
    ("2", "À déposer dans un conteneur ou dans une association"),
    (
        "3",
        "À déposer dans un conteneur, dans une association ou dans"
        " un magasin volontaire",
    ),
]

# Maps each consigne value to its SVG template path
CONSIGNE_SVG_TEMPLATES = {
    "1": "ui/components/infotri/svg/consigne-1.html",
    "2": "ui/components/infotri/svg/consigne-2.html",
    "3": "ui/components/infotri/svg/consigne-3.html",
}

# Maps each consigne value to its phrase SVG template path
PHRASE_SVG_TEMPLATES = {
    "1": "ui/components/infotri/svg/phrase-1.html",
    "2": "ui/components/infotri/svg/phrase-2.html",
    "3": "ui/components/infotri/svg/phrase-3.html",
}
