import datetime
import time
import urllib

from api_insee import ApiInsee
from django.conf import settings
from django.core.management.base import BaseCommand

from qfdmo.models import Acteur, CorrectionActeur, FinalActeur
from qfdmo.models.acteur import RevisionActeur

client = ApiInsee(key=settings.INSEE_KEY, secret=settings.INSEE_SECRET)


def call_api_insee(siren: str) -> dict | None:
    insee_data = None
    if len(siren) != 9:
        return insee_data
    try:
        insee_data = client.siren(
            siren,
            date=datetime.date.today().strftime("%Y-%m-%d"),
        ).get()
    except urllib.error.HTTPError as e:
        if "404" in str(e):
            pass
        if "429" in str(e):
            print("Too many requests, waiting 3 seconds")
            time.sleep(3)
            insee_data = call_api_insee(siren)
        else:
            raise e
    return insee_data


class Command(BaseCommand):
    help = "Get info from INSEE and save proposition of correction"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="limit the number of acteurs to process",
            type=int,
            default=None,
        )

    def handle(self, *args, **options):
        result = input(
            "Avant de commencer, avez vous bien mis à jour les vues matérialisées ?"
            " (y/N)"
        )
        if result.lower() != "y":
            print(
                "Veuillez mettre à jour les vues matérialisées avant de lancer ce"
                " script"
            )
            return
        nb_acteur_limit = options.get("limit")

        final_acteurs = (
            FinalActeur.objects.exclude(siret__isnull=True)
            .exclude(siret="")
            .exclude(
                identifiant_unique__in=CorrectionActeur.objects.values_list(
                    "identifiant_unique", flat=True
                ).filter(
                    source="INSEE",
                    cree_le__gte=datetime.datetime.now() - datetime.timedelta(days=31),
                ),
            )
            .order_by("?")
        )

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]

        counter = 0
        for final_acteur in final_acteurs:
            counter += 1
            if counter % 10 == 0:
                time.sleep(3)
            print(final_acteur, " : ", final_acteur.siret)
            insee_data = call_api_insee(final_acteur.siret[:9])

            if (
                insee_data is not None
                and "uniteLegale" in insee_data
                and "periodesUniteLegale" in insee_data["uniteLegale"]
                and len(insee_data["uniteLegale"]["periodesUniteLegale"]) > 0
            ):
                acteur = Acteur.objects.get(
                    identifiant_unique=final_acteur.identifiant_unique
                )
                nom_officiel = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "denominationUniteLegale"
                ]
                acteur.nom_officiel = nom_officiel

                naf_principal = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "activitePrincipaleUniteLegale"
                ]
                acteur.naf_principal = naf_principal
                siren = insee_data["uniteLegale"]["siren"]
                siret = (
                    siren
                    + insee_data["uniteLegale"]["periodesUniteLegale"][0][
                        "nicSiegeUniteLegale"
                    ]
                )
                acteur.siret = siret
                acteur.save()
                revision_acteurs = RevisionActeur.objects.filter(
                    identifiant_unique=final_acteur.identifiant_unique
                )
                if len(revision_acteurs) == 1:
                    if acteur.nom_officiel != nom_officiel:
                        revision_acteur = revision_acteurs[0]
                        revision_acteur.nom_officiel = nom_officiel
                    revision_acteur = revision_acteurs[0]
                    revision_acteur.siret = None
                    revision_acteur.save()
                elif len(revision_acteurs) == 0 and acteur.nom_officiel != nom_officiel:
                    RevisionActeur.objects.create(
                        identifiant_unique=final_acteur.identifiant_unique,
                        nom_officiel=nom_officiel,
                    )
            else:
                CorrectionActeur.objects.create(
                    source="INSEE",
                    siret=None,
                    resultat_brute_source="{}",
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                )


###
# Exemple de réponse de l'API INSEE
###

# DINUM_A_DATE = {
#     "header": {"statut": 200, "message": "OK"},
#     "uniteLegale": {
#         "siren": "130025265",
#         "statutDiffusionUniteLegale": "O",
#         "dateCreationUniteLegale": "2017-05-24",
#         "sigleUniteLegale": "DINUM",
#         "sexeUniteLegale": None,
#         "prenom1UniteLegale": None,
#         "prenom2UniteLegale": None,
#         "prenom3UniteLegale": None,
#         "prenom4UniteLegale": None,
#         "prenomUsuelUniteLegale": None,
#         "pseudonymeUniteLegale": None,
#         "identifiantAssociationUniteLegale": None,
#         "trancheEffectifsUniteLegale": "22",
#         "anneeEffectifsUniteLegale": "2020",
#         "dateDernierTraitementUniteLegale": "2023-01-25T16:46:56",
#         "nombrePeriodesUniteLegale": 2,
#         "categorieEntreprise": "PME",
#         "anneeCategorieEntreprise": "2020",
#         "periodesUniteLegale": [
#             {
#                 "dateFin": None,
#                 "dateDebut": "2019-10-25",
#                 "etatAdministratifUniteLegale": "A",
#                 "changementEtatAdministratifUniteLegale": False,
#                 "nomUniteLegale": None,
#                 "changementNomUniteLegale": False,
#                 "nomUsageUniteLegale": None,
#                 "changementNomUsageUniteLegale": False,
#                 "denominationUniteLegale": "DIRECTION INTERMINISTERIELLE DU …",
#                 "changementDenominationUniteLegale": True,
#                 "denominationUsuelle1UniteLegale": None,
#                 "denominationUsuelle2UniteLegale": None,
#                 "denominationUsuelle3UniteLegale": None,
#                 "changementDenominationUsuelleUniteLegale": False,
#                 "categorieJuridiqueUniteLegale": "7120",
#                 "changementCategorieJuridiqueUniteLegale": False,
#                 "activitePrincipaleUniteLegale": "84.11Z",
#                 "nomenclatureActivitePrincipaleUniteLegale": "NAFRev2",
#                 "changementActivitePrincipaleUniteLegale": False,
#                 "nicSiegeUniteLegale": "00013",
#                 "changementNicSiegeUniteLegale": False,
#                 "economieSocialeSolidaireUniteLegale": "N",
#                 "changementEconomieSocialeSolidaireUniteLegale": True,
#                 "societeMissionUniteLegale": None,
#                 "changementSocieteMissionUniteLegale": False,
#                 "caractereEmployeurUniteLegale": "N",
#                 "changementCaractereEmployeurUniteLegale": False,
#             }
#         ],
#     },
# }

# DINUM = {
#     "header": {"statut": 200, "message": "OK"},
#     "uniteLegale": {
#         "siren": "130025265",
#         "statutDiffusionUniteLegale": "O",
#         "dateCreationUniteLegale": "2017-05-24",
#         "sigleUniteLegale": "DINUM",
#         "sexeUniteLegale": None,
#         "prenom1UniteLegale": None,
#         "prenom2UniteLegale": None,
#         "prenom3UniteLegale": None,
#         "prenom4UniteLegale": None,
#         "prenomUsuelUniteLegale": None,
#         "pseudonymeUniteLegale": None,
#         "identifiantAssociationUniteLegale": None,
#         "trancheEffectifsUniteLegale": "22",
#         "anneeEffectifsUniteLegale": "2020",
#         "dateDernierTraitementUniteLegale": "2023-01-25T16:46:56",
#         "nombrePeriodesUniteLegale": 2,
#         "categorieEntreprise": "PME",
#         "anneeCategorieEntreprise": "2020",
#         "periodesUniteLegale": [
#             {
#                 "dateFin": None,
#                 "dateDebut": "2019-10-25",
#                 "etatAdministratifUniteLegale": "A",
#                 "changementEtatAdministratifUniteLegale": False,
#                 "nomUniteLegale": None,
#                 "changementNomUniteLegale": False,
#                 "nomUsageUniteLegale": None,
#                 "changementNomUsageUniteLegale": False,
#                 "denominationUniteLegale": "DIRECTION INTERMINISTERIELLE DU …",
#                 "changementDenominationUniteLegale": True,
#                 "denominationUsuelle1UniteLegale": None,
#                 "denominationUsuelle2UniteLegale": None,
#                 "denominationUsuelle3UniteLegale": None,
#                 "changementDenominationUsuelleUniteLegale": False,
#                 "categorieJuridiqueUniteLegale": "7120",
#                 "changementCategorieJuridiqueUniteLegale": False,
#                 "activitePrincipaleUniteLegale": "84.11Z",
#                 "nomenclatureActivitePrincipaleUniteLegale": "NAFRev2",
#                 "changementActivitePrincipaleUniteLegale": False,
#                 "nicSiegeUniteLegale": "00013",
#                 "changementNicSiegeUniteLegale": False,
#                 "economieSocialeSolidaireUniteLegale": "N",
#                 "changementEconomieSocialeSolidaireUniteLegale": True,
#                 "societeMissionUniteLegale": None,
#                 "changementSocieteMissionUniteLegale": False,
#                 "caractereEmployeurUniteLegale": "N",
#                 "changementCaractereEmployeurUniteLegale": False,
#             },
#             {
#                 "dateFin": "2019-10-24",
#                 "dateDebut": "2017-05-24",
#                 "etatAdministratifUniteLegale": "A",
#                 "changementEtatAdministratifUniteLegale": False,
#                 "nomUniteLegale": None,
#                 "changementNomUniteLegale": False,
#                 "nomUsageUniteLegale": None,
#                 "changementNomUsageUniteLegale": False,
#                 "denominationUniteLegale": "DIRECTION INTERMINISTERIELLE DU …",
#                 "changementDenominationUniteLegale": False,
#                 "denominationUsuelle1UniteLegale": None,
#                 "denominationUsuelle2UniteLegale": None,
#                 "denominationUsuelle3UniteLegale": None,
#                 "changementDenominationUsuelleUniteLegale": False,
#                 "categorieJuridiqueUniteLegale": "7120",
#                 "changementCategorieJuridiqueUniteLegale": False,
#                 "activitePrincipaleUniteLegale": "84.11Z",
#                 "nomenclatureActivitePrincipaleUniteLegale": "NAFRev2",
#                 "changementActivitePrincipaleUniteLegale": False,
#                 "nicSiegeUniteLegale": "00013",
#                 "changementNicSiegeUniteLegale": False,
#                 "economieSocialeSolidaireUniteLegale": None,
#                 "changementEconomieSocialeSolidaireUniteLegale": False,
#                 "societeMissionUniteLegale": None,
#                 "changementSocieteMissionUniteLegale": False,
#                 "caractereEmployeurUniteLegale": "N",
#                 "changementCaractereEmployeurUniteLegale": False,
#             },
#         ],
#     },
# }

# CAMAIEU_A_DATE = {
#     "header": {"statut": 200, "message": "OK"},
#     "uniteLegale": {
#         "siren": "345086177",
#         "statutDiffusionUniteLegale": "O",
#         "dateCreationUniteLegale": "1988-01-01",
#         "sigleUniteLegale": None,
#         "sexeUniteLegale": None,
#         "prenom1UniteLegale": None,
#         "prenom2UniteLegale": None,
#         "prenom3UniteLegale": None,
#         "prenom4UniteLegale": None,
#         "prenomUsuelUniteLegale": None,
#         "pseudonymeUniteLegale": None,
#         "identifiantAssociationUniteLegale": None,
#         "trancheEffectifsUniteLegale": "00",
#         "anneeEffectifsUniteLegale": "2020",
#         "dateDernierTraitementUniteLegale": "2023-01-06T13:51:37",
#         "nombrePeriodesUniteLegale": 9,
#         "categorieEntreprise": "ETI",
#         "anneeCategorieEntreprise": "2020",
#         "periodesUniteLegale": [
#             {
#                 "dateFin": None,
#                 "dateDebut": "2022-06-14",
#                 "etatAdministratifUniteLegale": "A",
#                 "changementEtatAdministratifUniteLegale": False,
#                 "nomUniteLegale": None,
#                 "changementNomUniteLegale": False,
#                 "nomUsageUniteLegale": None,
#                 "changementNomUsageUniteLegale": False,
#                 "denominationUniteLegale": "CAMAIEU INTERNATIONAL",
#                 "changementDenominationUniteLegale": False,
#                 "denominationUsuelle1UniteLegale": None,
#                 "denominationUsuelle2UniteLegale": None,
#                 "denominationUsuelle3UniteLegale": None,
#                 "changementDenominationUsuelleUniteLegale": False,
#                 "categorieJuridiqueUniteLegale": "5710",
#                 "changementCategorieJuridiqueUniteLegale": False,
#                 "activitePrincipaleUniteLegale": "47.71Z",
#                 "nomenclatureActivitePrincipaleUniteLegale": "NAFRev2",
#                 "changementActivitePrincipaleUniteLegale": False,
#                 "nicSiegeUniteLegale": "02461",
#                 "changementNicSiegeUniteLegale": False,
#                 "economieSocialeSolidaireUniteLegale": "N",
#                 "changementEconomieSocialeSolidaireUniteLegale": False,
#                 "societeMissionUniteLegale": "N",
#                 "changementSocieteMissionUniteLegale": True,
#                 "caractereEmployeurUniteLegale": "O",
#                 "changementCaractereEmployeurUniteLegale": False,
#             }
#         ],
#     },
# }
