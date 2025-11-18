from django.core.management.base import BaseCommand

from qfdmo.models import LabelQualite


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        LabelQualite.objects.filter(
            code__in=["ess", "reparacteur", "bonusrepar"]
        ).update(filtre=True)

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

        LabelQualite.objects.filter(code="bonusrepar").update(
            filtre_label=(
                "Masquer les lieux qui réparent uniquement les produits de "
                "leurs marques"
            ),
            filtre_texte_d_aide=(
                "Les adresses ne réparant que les produits de leur propre "
                "marque n'apparaîtront pas si cette case est cochée. "
                "(uniquement valable lorsque l'action « réparer » est "
                "sélectionnée)"
            ),
        )

        self.stdout.write(self.style.SUCCESS("Labels mis à jour"))
