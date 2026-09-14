"""Résolution d'un libellé d'objet vers sa fiche.

Vit hors du paquet `views` : le formulaire en a besoin, et `views/__init__`
importe les vues qui importent le formulaire — l'y laisser créait un cycle.
"""

# Chaque sous-classe de SearchTerm nomme différemment son libellé : il n'existe
# pas de champ commun à interroger.
CHAMPS_DE_LIBELLE = (
    ("ProduitPageSearchTerm", "searchable_title"),
    ("SearchTag", "name"),
    ("Synonyme", "nom"),
)

# Chaque sous-classe nomme aussi différemment sa relation vers la fiche.
RELATIONS_VERS_LA_FICHE = ("produit_page", "page")


def fiche_du_libelle(libelle: str):
    """Fiche correspondant à un libellé exact, pour une URL partagée.

    Renvoie la `ProduitPage` elle-même, pas son slug : l'appelant en a besoin
    telle quelle, et la lui rendre évite de la recharger juste après.

    L'autocomplétion renvoie le slug avec chaque suggestion ; ce chemin sert
    quand l'usager arrive par un lien qui ne porte que le texte. La recherche
    est exacte, pas floue : deviner sur une saisie approximative ouvrirait la
    mauvaise fiche sans que l'usager comprenne pourquoi.
    """
    from qfdmd import models

    # Chaque sous-classe range son libellé dans un champ différent : trois
    # requêtes indexées valent mieux que parcourir les 2 271 termes en Python,
    # ce qui coûtait 263 ms.
    for nom_modele, champ in CHAMPS_DE_LIBELLE:
        modele = getattr(models, nom_modele)
        for terme in modele.objects.filter(**{f"{champ}__iexact": libelle})[:5]:
            if page := fiche_de(terme):
                return page
    return None


def fiche_de(terme):
    """La `ProduitPage` d'un terme, ou None s'il n'en cible aucune."""
    from django.core.exceptions import ObjectDoesNotExist

    for relation in RELATIONS_VERS_LA_FICHE:
        try:
            page = getattr(terme, relation, None)
        except ObjectDoesNotExist:
            continue
        if page is not None and getattr(page, "slug", None):
            return page
    return None
