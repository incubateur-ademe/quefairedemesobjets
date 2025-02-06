import requests
from django.core.management.base import BaseCommand

from qfdmd.models import Lien, Produit, ProduitLien, Synonyme

ADEME_PRODUITS_URL = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/"
    "que-faire-de-mes-dechets-produits/lines?size=10000"
)

ADEME_LIENS_URL = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/"
    "que-faire-de-mes-dechets-liens/lines?size=10000"
)


class Command(BaseCommand):
    help = "Import des produits depuis data.ademe.fr"

    def import_produits(self):
        data_ademe_r = requests.get(ADEME_PRODUITS_URL)
        nb_produit_created = 0
        nb_produit_updated = 0
        nb_synonyme_created = 0
        nb_synonyme_updated = 0
        for line in data_ademe_r.json()["results"]:
            synonymes_existants = line.get("Synonymes_existants", "")
            nom = line.get("Nom", "")
            produit, created = Produit.objects.update_or_create(
                id=line["ID"],  # ID: string
                defaults={
                    "nom": nom,
                    "synonymes_existants": synonymes_existants,
                    "code": line.get("Code", ""),
                    "bdd": line.get("Bdd", ""),
                    "comment_les_eviter": line.get("Comment_les_eviter_?", ""),
                    "qu_est_ce_que_j_en_fais": line.get(
                        "Qu'est-ce_que_j'en_fais_?", ""
                    ),
                    "que_va_t_il_devenir": line.get("Que_va-t-il_devenir_?", ""),
                    "nom_eco_organisme": line.get("nom_eco_organisme", ""),
                    "filieres_rep": line.get("filieres_REP", ""),
                    "slug": line["slug"],
                },
            )
            if created:
                nb_produit_created += 1
            else:
                nb_produit_updated += 1
            synonymes = [s.strip() for s in synonymes_existants.split("/") if s.strip()]
            synonymes = synonymes + [nom]
            for synonyme_nom in synonymes:
                _, created = Synonyme.objects.update_or_create(
                    nom=synonyme_nom, defaults={"produit_id": produit.id}
                )
                if created:
                    nb_synonyme_created += 1
                else:
                    nb_synonyme_updated += 1
        return {
            "nb_produit_created": nb_produit_created,
            "nb_produit_updated": nb_produit_updated,
            "nb_synonyme_created": nb_synonyme_created,
            "nb_synonyme_updated": nb_synonyme_updated,
        }

    def import_liens(self):
        data_ademe_liens_r = requests.get(ADEME_LIENS_URL)
        nb_lien_created = 0
        nb_lien_updated = 0
        for index, line in enumerate(data_ademe_liens_r.json()["results"]):
            lien, created = Lien.objects.update_or_create(
                titre_du_lien=line["Titre_du_lien"],
                defaults={
                    "url": line["URL"],
                    "description": line.get("Description", ""),
                },
            )

            produit_ids = [p.strip() for p in line["Produits_associes"].split(";")]
            for produit_id in produit_ids:
                if not produit_id.isnumeric():
                    continue
                try:
                    produit = Produit.objects.get(id=produit_id)
                    ProduitLien.objects.update_or_create(
                        lien=lien, produit=produit, defaults={"poids": index}
                    )
                except Produit.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"Produit avec ID {produit_id} n'existe pas")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            "Erreur lors de l'ajout du produit avec IDs"
                            f" {line['Produits_associes']}: {e}"
                        )
                    )

            if created:
                nb_lien_created += 1
            else:
                nb_lien_updated += 1
        return {"nb_lien_created": nb_lien_created, "nb_lien_updated": nb_lien_updated}

    def handle(self, *args, **options):
        result_import_produits = self.import_produits()
        result_import_liens = self.import_liens()

        self.stdout.write(
            self.style.SUCCESS(
                "Import des produits depuis data.ademe.fr terminé: "
                f"{result_import_produits['nb_produit_created']} créés, "
                f"{result_import_produits['nb_produit_updated']} mis à jour"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Import des synonymes depuis data.ademe.fr terminé: "
                f"{result_import_produits['nb_synonyme_created']} créés, "
                f"{result_import_produits['nb_synonyme_updated']} mis à jour"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Import des liens depuis data.ademe.fr terminé: "
                f"{result_import_liens['nb_lien_created']} créés, "
                f"{result_import_liens['nb_lien_updated']} mis à jour"
            )
        )
