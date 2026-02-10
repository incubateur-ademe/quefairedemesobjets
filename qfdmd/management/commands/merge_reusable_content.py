import logging

from django.core.management.base import BaseCommand

from qfdmd.models import ProduitPage, ReusableContent

logger = logging.getLogger(__name__)


def update_block_inplace(streamblock, base_content, batch):
    for block in streamblock.blocks_by_name("reusable"):
        if block.value in batch and block.value != base_content:
            block.value = base_content


def merge_reusable_content():
    done = []
    for reusable_content in ReusableContent.objects.all():
        base_title = "-".join(reusable_content.title.split("-")[:-2])
        if base_title in done:
            continue

        batch = ReusableContent.objects.filter(title__startswith=f"{base_title}-")

        if batch.count() != 4:
            logger.error(
                f"The batch length is not expected - {batch.count()=} - {base_title=}"
            )
            continue

        try:
            base_content = ReusableContent.objects.get(title=base_title)
        except ReusableContent.DoesNotExist:
            base_content = batch.first()

            # Clone and create a new reusable content
            base_content.id = None
            base_content.title = base_title
            if base_content is not None:
                base_content.masculin_singulier = batch.get(genre="m", nombre=1).content
                base_content.masculin_pluriel = batch.get(genre="m", nombre=2).content
                base_content.feminin_singulier = batch.get(genre="f", nombre=1).content
                base_content.feminin_pluriel = batch.get(genre="f", nombre=2).content
                base_content.genre = ""
                base_content.nombre = None
                base_content.save()

        for page in ProduitPage.objects.all():
            update_block_inplace(page.body, base_content, batch)

            for block in page.body.blocks_by_name("tabs"):
                for subblock in block.value:
                    update_block_inplace(subblock.value["content"], base_content, batch)

            page.save()


class Command(BaseCommand):
    help = "Merge reusable content based on their titles"

    def handle(self, *args, **options):
        merge_reusable_content()
