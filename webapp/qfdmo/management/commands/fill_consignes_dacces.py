from django.core.management.base import BaseCommand

from qfdmo.models.acteur import Acteur, ActeurStatus, RevisionActeur

consignes_dacces = (
    "Un badge d'accès peut vous être demandé à l’entrée."
    " Nous vous invitons à vous renseigner avant de vous rendre sur place."
)


def add_consignes_dacces():
    for acteur in Acteur.objects.filter(acteur_type__code="decheterie"):
        print("ACTEUR", acteur.identifiant_unique)
        if acteur.statut != ActeurStatus.ACTIF:
            revision_acteur = RevisionActeur.objects.filter(
                identifiant_unique=acteur.identifiant_unique
            ).first()
            if revision_acteur is None or revision_acteur.statut != ActeurStatus.ACTIF:
                continue
        else:
            revision_acteur = acteur.get_or_create_revision()
        parent_revision_acteur = revision_acteur.parent
        if (
            parent_revision_acteur is None
            and not revision_acteur.consignes_dacces
            and revision_acteur.statut == ActeurStatus.ACTIF
        ):
            print("REVISION ACTEUR", revision_acteur.identifiant_unique)
            revision_acteur.consignes_dacces = consignes_dacces
            revision_acteur.save()
        elif (
            parent_revision_acteur is not None
            and not parent_revision_acteur.consignes_dacces
            and parent_revision_acteur.statut == ActeurStatus.ACTIF
        ):
            print("PARENT REVISION ACTEUR", parent_revision_acteur.identifiant_unique)
            parent_revision_acteur.consignes_dacces = consignes_dacces
            parent_revision_acteur.save()


class Command(BaseCommand):
    help = "Initialisation des consignes d'accès pour les déchèteries"

    def handle(self, *args, **options):
        add_consignes_dacces()
