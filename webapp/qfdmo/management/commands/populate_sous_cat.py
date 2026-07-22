import random

from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, PropositionService, RevisionPropositionService
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet

MAPPINGS = [
    {
        "existing_sous_categorie": "outil de bricolage et jardinage",
        "new_sous_categories": [
            "Machines et appareils motorises thermiques",
        ],
        "actions": ["donner", "mettreenlocation"],
    },
    {
        "existing_sous_categorie": "outil de bricolage et jardinage",
        "new_sous_categories": [
            "ABJ_electrique",  # Outil de bricolage et jardinage électrique
        ],
        "actions": [
            "donner",
            "reparer",
            "revendre",
            "acheter",
            "louer",
            "mettreenlocation",
            "preter",
            "emprunter",
        ],
    },
    {
        "existing_sous_categorie": "meuble",
        "new_sous_categories": [
            "Sièges - Éléments d'ameublement",
        ],
        "actions": ["donner", "reparer", "revendre", "acheter", "louer"],
    },
    {
        "existing_sous_categorie": "meuble",
        "new_sous_categories": ["Literie - Éléments d'ameublement"],
        "actions": ["donner", "reparer", "revendre", "acheter"],
    },
    {
        "existing_sous_categorie": "decoration",
        "new_sous_categories": ["Décoration textile - Éléments d'ameublement"],
        "actions": ["donner", "revendre", "acheter"],
    },
    {
        "existing_sous_categorie": "materiau du batiment reemployable",
        "new_sous_categories": [
            "Métal - PMCB (produits et matériaux de construction du bâtiment)",
            "Huisseries (produits et matériaux de construction du bâtiment)",
            "Bois - PMCB (produits et matériaux de construction du bâtiment)",
        ],
        "actions": ["donner", "acheter"],
    },
    {
        "existing_sous_categorie": "gros electromenager (hors refrigerant)",
        "new_sous_categories": ["Panneaux photovoltaïques"],
        "actions": ["donner", "revendre", "preter"],
    },
    {
        "existing_sous_categorie": "velo",
        "new_sous_categories": ["JELS_Mobilite_electrique"],
        "actions": ["donner", "revendre", "preter"],
    },
    {
        "existing_sous_categorie": "gros electromenager (hors refrigerant)",
        "new_sous_categories": ["JELS_Mobilite_electrique"],
        "actions": ["preter", "trier"],
    },
    {
        "existing_sous_categorie": "jouet",
        "new_sous_categories": ["JELS_Mobilite_electrique"],
        "actions": ["donner", "revendre"],
    },
    {
        "existing_sous_categorie": "instrument de musique",
        "new_sous_categories": ["instrument_musique_electrique"],
        "actions": ["donner", "reparer", "revendre", "acheter"],
    },
    {
        "existing_sous_categorie": "gros electromenager (hors refrigerant)",
        "new_sous_categories": ["instrument_musique_electrique"],
        "actions": ["trier"],
    },
    {
        "existing_sous_categorie": "medicaments",
        "new_sous_categories": ["dasri"],
        "actions": ["trier"],
    },
]


def assign_new_sous_cat(self, mappings=MAPPINGS) -> None:

    # vérification de tous les codes de sous catégories et actions
    existing_error = False
    for mapping in mappings:
        try:
            SousCategorieObjet.objects.get(code=mapping["existing_sous_categorie"])
        except SousCategorieObjet.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"La sous catégorie `{mapping['existing_sous_categorie']}` n'existe"
                    " pas dans la base de données"
                )
            )
            existing_error = True
        for code in mapping["new_sous_categories"]:
            try:
                SousCategorieObjet.objects.get(code=code)
            except SousCategorieObjet.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"La sous catégorie `{code}` n'existe pas dans la base de"
                        " données"
                    )
                )
                existing_error = True
        for code in mapping["actions"]:
            try:
                Action.objects.get(code=code)
            except Action.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"L'action `{code}` n'existe pas dans la base de données"
                    )
                )
                existing_error = True
    if existing_error:
        return

    # Révision de proposition de service
    # sur proposition de service, si pas revision de proposition de service alors on
    #  crée une révision et on corrige les revision de proposition de service
    for mapping in mappings:
        self.stdout.write(
            self.style.SUCCESS(
                f"""
Assigning new sous categories: {mapping['new_sous_categories']}
To existing sous categorie: {mapping['existing_sous_categorie']}
With actions: {mapping['actions']}
"""
            )
        )
        existing_sous_categorie = mapping["existing_sous_categorie"]

        acteur_ids_in_mapping_without_revision = (
            PropositionService.objects.filter(
                sous_categories__code=existing_sous_categorie,
                action__code__in=mapping["actions"],
            )
            .exclude(
                acteur_id__in=RevisionPropositionService.objects.values_list(
                    "acteur_id", flat=True
                )
            )
            .values_list("acteur_id", flat=True)
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Acteurs concernés sans révision : "
                f"{len(acteur_ids_in_mapping_without_revision)} acteurs. \n"
                "Création des révisions pour ces acteurs"
            )
        )

        acteurs = Acteur.objects.filter(
            identifiant_unique__in=acteur_ids_in_mapping_without_revision
        )
        for acteur in acteurs:
            acteur.get_or_create_revision()

        self.stdout.write(
            self.style.SUCCESS(
                "Assignation des nouvelles sous catégories aux révisions concernées"
            )
        )

        # Collecter les nouvelles sous catégories
        new_sous_categorie_objets = [
            SousCategorieObjet.objects.get(code=code)
            for code in mapping["new_sous_categories"]
        ]

        # Ajouter les nouvelles sous catégories aux RevisionPropositionService
        # concernées
        prop_services = RevisionPropositionService.objects.filter(
            sous_categories__code=existing_sous_categorie,
            action__code__in=mapping["actions"],
        )

        # récupérer les action_id unique des objets prop_services
        acteur_ids = prop_services.values_list("acteur_id", flat=True).distinct()

        self.stdout.write(
            self.style.SUCCESS(
                f"Assignation des nouvelles sous catégories aux {acteur_ids.count()}"
                " révisions concernées"
            )
        )
        sample_acteur_ids = random.sample(list(acteur_ids), min(10, len(acteur_ids)))
        self.stdout.write(f"Echantillon d'acteurs modifiés (10) : {sample_acteur_ids}")

        for prop_service in prop_services:
            prop_service.sous_categories.add(*new_sous_categorie_objets)


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def handle(self, *args, **options):
        assign_new_sous_cat(self)
