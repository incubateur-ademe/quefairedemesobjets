import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmo.models import (
    ActeurService,
    ActeurType,
    Action,
    LVAOBase,
    LVAOBaseRevision,
    SousCategorieObjet,
)

mapping_fields_base_db = {
    "revision_id": "lvao_revision_id",
    "node_id": "lvao_node_id",
    "title": "nom",
    "TypeActeur": "acteur_type",
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
    "Activite": "acteur_services",
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
        count = 0
        filepath: Path = options.get(
            "filepath", settings.BASE_DIR / "backup_db.bak" / "Base_20221218_Depart.csv"
        )
        with open(filepath, newline="") as csvfile:
            spamreader = csv.reader(csvfile, delimiter=";", quotechar='"')

            headers = next(spamreader)
            next(spamreader)
            next(spamreader)
            for fields in spamreader:
                count += 1

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
                    lvao_base, created = LVAOBase.objects.get_or_create(
                        identifiant_unique=new_entite["identifiant_unique"],
                        defaults={"nom": new_entite["nom"]},
                    )
                    del new_entite["identifiant_unique"]
                    new_entite["lvao_base"] = lvao_base
                    new_entite["acteur_type"] = ActeurType.objects.get(
                        lvao_id=new_entite["acteur_type"]
                    )
                    new_entite["longitude"] = (
                        float(new_entite["longitude"])
                        if new_entite["longitude"]
                        else None
                    )
                    new_entite["latitude"] = (
                        float(new_entite["latitude"])
                        if new_entite["latitude"]
                        else None
                    )
                    new_entite["multi_base"] = bool(float(new_entite["multi_base"]))

                    (
                        lvao_base_revision,
                        _,
                    ) = LVAOBaseRevision.objects.get_or_create(
                        lvao_revision_id=new_entite["lvao_revision_id"],
                        defaults=new_entite,
                    )
                    lvao_base_revision.actions.set(
                        Action.objects.filter(
                            lvao_id__in=new_entite_relationships["actions"]
                        )
                    )
                    lvao_base_revision.acteur_services.set(
                        ActeurService.objects.filter(
                            lvao_id__in=new_entite_relationships["acteur_services"]
                        )
                    )
                    lvao_base_revision.sous_categories.set(
                        SousCategorieObjet.objects.filter(
                            lvao_id__in=new_entite_relationships["sous_categories"]
                        )
                    )
                    print(
                        f"{count} - {lvao_base_revision.nom} "
                        f"{'created' if created else 'new revision'}"
                    )
