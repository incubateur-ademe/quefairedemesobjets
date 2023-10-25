import datetime
import time
import urllib

from api_insee import ApiInsee
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from qfdmo.models import (
    Acteur,
    CorrecteurActeurStatus,
    CorrectionActeur,
    FinalActeur,
    RevisionActeur,
)

client = ApiInsee(key=settings.INSEE_KEY, secret=settings.INSEE_SECRET)

SOURCE = "INSEE"


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
            FinalActeur.objects.annotate(siret_length=Length("siret"))
            .filter(siret_length=14)
            .exclude(
                identifiant_unique__in=CorrectionActeur.objects.values_list(
                    "identifiant_unique", flat=True
                ).filter(
                    source=SOURCE,
                    cree_le__gte=datetime.datetime.now() - datetime.timedelta(days=31),
                ),
            )
            .order_by("?")
        )

        if nb_acteur_limit is not None:
            final_acteurs = final_acteurs[:nb_acteur_limit]

        for final_acteur in final_acteurs:
            print(final_acteur, " : ", final_acteur.siret)
            insee_data = call_api_insee(final_acteur.siret[:9])
            if (
                insee_data is not None
                and "uniteLegale" in insee_data
                and "periodesUniteLegale" in insee_data["uniteLegale"]
                and len(insee_data["uniteLegale"]["periodesUniteLegale"]) > 0
            ):
                nom_officiel = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "denominationUniteLegale"
                ]
                naf_principal = insee_data["uniteLegale"]["periodesUniteLegale"][0][
                    "activitePrincipaleUniteLegale"
                ]
                siren = insee_data["uniteLegale"]["siren"]
                siret = (
                    siren
                    + insee_data["uniteLegale"]["periodesUniteLegale"][0][
                        "nicSiegeUniteLegale"
                    ]
                )
                acteurfields_to_update = {
                    "nom_officiel": nom_officiel,
                    "naf_principal": naf_principal,
                    "siret": siret,
                }
                _update_acteur(
                    final_acteur.identifiant_unique,
                    acteurfields_to_update,
                )

                CorrectionActeur.objects.create(
                    **acteurfields_to_update,
                    source=SOURCE,
                    resultat_brute_source=insee_data,
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                    correction_statut=CorrecteurActeurStatus.NOT_CHANGED,
                )
            else:
                CorrectionActeur.objects.create(
                    source=SOURCE,
                    siret=None,
                    resultat_brute_source="{}",
                    identifiant_unique=final_acteur.identifiant_unique,
                    final_acteur_id=final_acteur.identifiant_unique,
                )


def _update_acteur(identifiant_unique: str, actorfields_to_update: dict):
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    for field, value in actorfields_to_update.items():
        setattr(acteur, field, value)
    acteur.save()
    RevisionActeur.objects.filter(identifiant_unique=identifiant_unique).update(
        **{field: None for field, _ in actorfields_to_update.items()}
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
