from django.core.management.base import BaseCommand

from qfdmd.models import ReusableContent


def merge_reusable_content():
    done = []
    for reusable_content in ReusableContent.objects.all():
        base_title = "-".join(reusable_content.title.split("-")[:-2])
        if base_title in done:
            continue

        batch = ReusableContent.objects.filter(title__startswith=base_title)
        if batch.count() != 4:
            raise Exception("The batch length is not expected")

        base_content = batch.first()

        if base_content is not None:
            base_content.masculin_singulier = batch.get(genre="m", nombre=1)
            base_content.masculin_pluriel = batch.get(genre="m", nombre=2)
            base_content.feminin_singulier = batch.get(genre="m", nombre=1)
            base_content.feminin_pluriel = batch.get(genre="f", nombre=2)
            base_content.save()


class Command(BaseCommand):
    help = "Merge reusable content based on their titles"

    def handle(self, *args, **options):
        merge_reusable_content()
