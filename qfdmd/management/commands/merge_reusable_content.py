from django.core.management.base import BaseCommand

from qfdmd.models import FamilyPage, ProduitPage, ReusableContent


def merge_reusable_content():
    done = []
    for reusable_content in ReusableContent.objects.all():
        base_title = "-".join(reusable_content.title.split("-")[:-2])
        if base_title in done:
            continue

        batch = ReusableContent.objects.filter(title__startswith=base_title)

        if batch.count() != 4:
            print(f"The batch length is not expected - {batch.count()=}")
            continue

        base_content = batch.first()

        base_content.title = base_title
        if base_content is not None:
            base_content.masculin_singulier = batch.get(genre="m", nombre=1).content
            base_content.masculin_pluriel = batch.get(genre="m", nombre=2).content
            base_content.feminin_singulier = batch.get(genre="m", nombre=1).content
            base_content.feminin_pluriel = batch.get(genre="f", nombre=2).content
            base_content.genre = ""
            base_content.nombre = None
            base_content.save()

        for page in [*FamilyPage.objects.all(), *ProduitPage.objects.all()]:
            for block in page.body.blocks_by_name("reusable"):
                index = page.body.index(block)
                print(f"Block has index {index=}")
                if block.value in batch and block.value != base_content:
                    print(f"Update block {block=} on {page=}")
                    block.value = base_content
                # page.body[index] = block

            page.save()


class Command(BaseCommand):
    help = "Merge reusable content based on their titles"

    def handle(self, *args, **options):
        merge_reusable_content()
