"""Constants for Info-tri feature."""

# Categorie choices
CATEGORIE_CHOICES = [
    ("", "Sélectionnez une catégorie"),
    ("tous", "Tous"),
    ("chaussures", "Chaussures"),
    ("vetement", "Vêtement"),
    ("tissu", "Tissu"),
]

# Consigne choices
CONSIGNE_CHOICES = [
    ("", "Sélectionnez une consigne"),
    ("1", "À déposer dans un conteneur"),
    ("2", "À déposer dans un conteneur ou dans une association"),
    (
        "3",
        "À déposer dans un conteneur, dans une association ou dans"
        " un magasin volontaire",
    ),
]

# Valid values (excluding empty choice)
VALID_CATEGORIES = [choice[0] for choice in CATEGORIE_CHOICES if choice[0]]
VALID_CONSIGNES = [choice[0] for choice in CONSIGNE_CHOICES if choice[0]]
