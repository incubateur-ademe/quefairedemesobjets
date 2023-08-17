from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import CategorieObjet as Category
from qfdmo.models import SousCategorieObjet as SubCategory

object_categories = [
    [
        171,
        "Gros électroménager (froid)",
        "Electroménager",
        "C_01",
        "GROS ELECTROMENAGER (FROID)",
    ],
    [
        172,
        "Gros électroménager (hors froid)",
        "Electroménager",
        "C_02",
        "GROS ELECTROMENAGER (HORS FROID)",
    ],
    [173, "Petit électroménager", "Electroménager", "C_03", "PETIT ELECTROMENAGER"],
    [174, "Écrans", "Image & son & Informatique", "C_04", "ECRANS"],
    [
        176,
        "Matériel informatique",
        "Image & son & Informatique",
        "C_05",
        "MATERIEL INFORMATIQUE",
    ],
    [
        177,
        "Hifi/vidéo (hors écrans)",
        "Image & son & Informatique",
        "C_06",
        "HIFI/VIDEO (HORS ECRANS)",
    ],
    [
        175,
        "Smartphones/tablettes/consoles",
        "Image & son & Informatique",
        "C_07",
        "SMARTPHONES/TABLETTES/CONSOLES",
    ],
    [178, "Photo/ciné", "Image & son & Informatique", "C_08", "PHOTO/CINE"],
    [
        179,
        "Autres équipements électroniques",
        "Image & son & Informatique",
        "C_09",
        "AUTRES EQUIPEMENTS ELECTRONIQUES",
    ],
    [180, "CD/DVD/jeux vidéo", "Livres & Multimedia", "C_10", "CD/DVD/JEUX VIDEO"],
    [181, "Livres", "Livres & Multimedia", "C_11", "LIVRES"],
    [
        182,
        "Instruments de musique",
        "Equipements de loisir",
        "C_12",
        "INSTRUMENTS DE MUSIQUE",
    ],
    [
        183,
        "Outillage (bricolage/jardinage)",
        "Bricolage / Jardinage",
        "C_13",
        "OUTILLAGE (BRICOLAGE/JARDINAGE)",
    ],
    [
        184,
        "Jardin (mobilier, accessoires)",
        "Equipements de loisir",
        "C_14",
        "JARDIN (MOBILIER, ACCESSOIRES)",
    ],
    [185, "Mobilier", "Mobilier et décoration", "C_15", "MOBILIER"],
    [186, "Décoration", "Mobilier et décoration", "C_16", "DECORATION"],
    [187, "Luminaires", "Mobilier et décoration", "C_17", "LUMINAIRES"],
    [189, "Vaisselle", "Mobilier et décoration", "C_18", "VAISSELLE"],
    [190, "Linge de maison", "Vêtements & Accessoires", "C_19", "LINGE DE MAISON"],
    [191, "Puériculture", "Produits divers", "C_20", "PUERICULTURE"],
    [192, "Jouets", "Equipements de loisir", "C_21", "JOUETS"],
    [193, "Vêtements", "Vêtements & Accessoires", "C_22", "VETEMENTS"],
    [194, "Maroquinerie", "Vêtements & Accessoires", "C_23", "MAROQUINERIE"],
    [195, "Chaussures", "Vêtements & Accessoires", "C_24", "CHAUSSURES"],
    [
        196,
        "Bijou, montre, horlogerie",
        "Bijou, montre, horlogerie",
        "C_25",
        "BIJOU, MONTRE, HORLOGERIE",
    ],
    [197, "Vélos", "Equipements de loisir", "C_26", "VELOS"],
    [
        198,
        "Autre matériel de sport",
        "Equipements de loisir",
        "C_27",
        "AUTRE MATERIEL DE SPORT",
    ],
    [199, "Matériel médical", "Produits divers", "C_28", "MATERIEL MEDICAL"],
    [None, "Tout type", "Tout type", "", "C_29", "TOUT TYPE"],
]


class Command(BaseCommand):
    # pylint: disable=R0912,R0914,R0915
    def handle(self, *args, **options):
        with transaction.atomic():
            Category.objects.all().delete()
            SubCategory.objects.all().delete()
            for object_category in object_categories:
                category, _ = Category.objects.get_or_create(nom=object_category[2])
                SubCategory.objects.get_or_create(
                    nom=object_category[1],
                    lvao_id=object_category[0],
                    categorie=category,
                    code=object_category[3],
                )
