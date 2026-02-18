from django.core.management.base import BaseCommand

from qfdmo.models import GroupeAction, LabelQualite


class Command(BaseCommand):
    help = "Post-deployment command for mode_liste feature"

    def handle(self, *args, **options):
        # Update LabelQualite filtre fields
        LabelQualite.objects.filter(code__in=["ess", "reparacteur"]).update(filtre=True)

        LabelQualite.objects.filter(code="ess").update(
            filtre_label="Lieux de l'économie sociale et solidaire",
            filtre_texte_d_aide=(
                "Afficher uniquement les adresses recensées comme relevant de "
                "l'économie sociale et solidaire. En savoir plus sur le site "
                "economie.gouv.fr"
            ),
        )

        LabelQualite.objects.filter(code="reparacteur").update(
            filtre_label="Lieux labellisés Répar'Acteurs",
            filtre_texte_d_aide=(
                "Afficher uniquement les artisans labellisés (uniquement "
                "valable lorsque l'action « réparer » est sélectionnée). "
                "Les Répar'Acteurs sont une initiative de la Chambre des "
                "Métiers et de l'Artisanat"
            ),
        )

        self.stdout.write(self.style.SUCCESS("Labels mis à jour"))

        # Update GroupeAction icons
        GroupeAction.objects.filter(icon="fr-icon-hand-heart-line").update(
            icon="fr-icon-hand-heart"
        )

        self.stdout.write(self.style.SUCCESS("Icônes GroupeAction mis à jour"))
