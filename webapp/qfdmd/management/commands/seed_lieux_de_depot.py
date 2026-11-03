from django.core.management.base import BaseCommand

from qfdmd.models import LieuDeDepot

LIEUX = [
    ("bac_de_tri", "Bac de tri", "yellow-tournesol"),
    ("conteneur_a_verre", "Conteneur à verre", "green-emeraude"),
    ("decheterie", "Déchèterie", "brown-caramel"),
    ("point_de_collecte", "Point de collecte", "blue-ecume"),
    ("ordures_menageres", "Ordures ménagères", "orange-terre-battue"),
    ("magasin", "Magasin", "pink-macaron"),
    ("bac_de_compostage", "Bac de compostage", "brown-caramel"),
    ("bois_de_chauffage", "Bois de chauffage", "orange-terre-battue"),
    ("entre_particuliers", "Entre particuliers", "beige-gris-galet"),
    ("reemploi", "Réemploi", "blue-cumulus"),
    ("structure_de_reemploi", "Structure de réemploi", "green-emeraude"),
    ("etablissement_de_sante", "Établissement de santé", "green-bourgeon"),
]


class Command(BaseCommand):
    help = "Create the missing lieux de dépôt, leaving existing ones untouched."

    def handle(self, *args, **options):
        created = sum(
            LieuDeDepot.objects.get_or_create(
                code=code, defaults={"libelle": libelle, "couleur": couleur}
            )[1]
            for code, libelle, couleur in LIEUX
        )
        self.stdout.write(f"{created} lieu(x) de dépôt créé(s)")
