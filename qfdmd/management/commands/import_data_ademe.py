import requests
from django.core.management.base import BaseCommand

from qfdmd.models import Produit


class Command(BaseCommand):
    help = "Import des produits depuis data.ademe.fr"

    def handle(self, *args, **options):
        data_ademe_r = requests.get(
            "https://data.ademe.fr/data-fair/api/v1/datasets/que-faire-de-mes-dechets-produits/lines?size=10000&select=ID%2CNom"
        )
        for line in data_ademe_r.json()["results"]:
            obj, created = Produit.objects.update_or_create(
                id=line["ID"], defaults={"libelle": line["Nom"]}
            )

            if created:
                print(f"produit ademe {obj.id} ajouté")
