from django.core.management.base import BaseCommand
from django.utils.text import slugify

from qfdmd.models import ProduitPage, SearchTag, TaggedSearchTag


class Command(BaseCommand):
    """
    This is useful only once, for the initial development of Synonymes
    de recherche (SearchTag) feature.
    Once this feature will be deployed on production, the sample database
    used for e2e testing will be populated with search terms and we won't
    need to generate fake ones.

    TODO: remove this command when Synonymes de recherche is live.
    """

    help = "Create a fake SearchTag for e2e test coverage of SearchTag link parameters"

    def handle(self, *args, **options):
        name = "canapé d'angle"
        slug = slugify(name, allow_unicode=True)

        try:
            meubles_page = ProduitPage.objects.get(id=270)
        except ProduitPage.DoesNotExist:
            self.stdout.write("ProduitPage id=270 not found, skipping")
            return

        tag, _ = SearchTag.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )

        if TaggedSearchTag.objects.filter(tag=tag).exists():
            self.stdout.write("SearchTag already linked, skipping")
            return

        TaggedSearchTag.objects.create(tag=tag, content_object=meubles_page)
        self.stdout.write("SearchTag 'canapé d'angle' created on Meubles page")
