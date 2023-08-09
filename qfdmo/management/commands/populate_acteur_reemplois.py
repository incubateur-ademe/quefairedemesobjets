from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import (
    ActeurReemploi,
    ActeurReemploiRevision,
    Action,
    EntiteService,
    EntiteType,
    SousCategorieObjet,
)

mapping_fields_base_db = {
    "revision_id": "lvao_revision_id",
    "node_id": "lvao_node_id",
    "title": "nom",
    "TypeActeur": "entite_type",
    "Adresse1": "adresse",
    "Adresse2": "adresse_complement",
    "CodePostal": "code_postal",
    "Ville": "ville",
    "url": "url",
    "email": "email",
    "latitude": "latitude",
    "longitude": "longitude",
    "Telephone": "telephone",
    "MultiBase": "multi_base",
    "UniqueId": "identifiant_unique",
    "NomCial": "nom_commercial",
    "RaisonSociale": "nom_officiel",
    "Published": "publie",
    "Manuel": "manuel",
    "Reparacteur": "label_reparacteur",
    "Siret": "siret",
    "BDD": "source_donnee",
    "ActeurId": "identifiant_externe",
}

mapping_many_to_many_base_db = {
    "Geste": "actions",
    "Activite": "services",
    "Objets": "sous_categories",
}


class Command(BaseCommand):
    help = "Injest local LVAO BASE csv file from local filepath"

    def add_arguments(self, parser):
        parser.add_argument(
            "filepath",
            type=Path,
            help="filepath to Base___.csv file extract from LVAO",
        )

    def handle(self, *args, **options):
        filepath: Path = options.get(
            "filepath", settings.BASE_DIR / "backup_db.bak" / "Base_20221218_Depart.csv"
        )
        base_file = open(filepath, "r")
        count = 0
        header_line = base_file.readline()
        headers = header_line.split(";")
        base_file.readline()  # ignore line with 1
        base_file.readline()  # ignore line with types
        while True:
            count += 1

            # Get next line from file
            line = base_file.readline()

            # if line is empty
            # end of file is reached
            if not line:
                break
            fields = line.split(";")

            new_entite = {
                mapping_fields_base_db[header]: fields[index].strip('" ')
                for index, header in enumerate(headers)
                if header in mapping_fields_base_db
            }
            new_entite_relationships = {
                mapping_many_to_many_base_db[header]: fields[index].split("|")
                for index, header in enumerate(headers)
                if header in mapping_many_to_many_base_db
            }
            with transaction.atomic():
                acteur_reemploi, created = ActeurReemploi.objects.get_or_create(
                    identifiant_unique=new_entite["identifiant_unique"],
                    defaults={"nom": new_entite["nom"]},
                )
                del new_entite["identifiant_unique"]
                new_entite["acteur_reemploi"] = acteur_reemploi
                new_entite["entite_type"] = EntiteType.objects.get(
                    lvao_id=new_entite["entite_type"]
                )
                new_entite["longitude"] = (
                    float(new_entite["longitude"]) if new_entite["longitude"] else None
                )
                new_entite["latitude"] = (
                    float(new_entite["latitude"]) if new_entite["latitude"] else None
                )
                new_entite["multi_base"] = bool(float(new_entite["multi_base"]))

                (
                    acteur_reemploi_revision,
                    _,
                ) = ActeurReemploiRevision.objects.get_or_create(
                    lvao_revision_id=new_entite["lvao_revision_id"],
                    defaults=new_entite,
                )
                acteur_reemploi_revision.actions.set(
                    Action.objects.filter(
                        lvao_id__in=new_entite_relationships["actions"]
                    )
                )
                acteur_reemploi_revision.services.set(
                    EntiteService.objects.filter(
                        lvao_id__in=new_entite_relationships["services"]
                    )
                )
                acteur_reemploi_revision.sous_categories.set(
                    SousCategorieObjet.objects.filter(
                        lvao_id__in=new_entite_relationships["sous_categories"]
                    )
                )
                print(
                    f"{count} - {acteur_reemploi_revision.nom} "
                    f"{'created' if created else 'new revision'}"
                )
