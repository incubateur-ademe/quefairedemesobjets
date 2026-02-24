from django.core.management.base import BaseCommand
from wagtail.models import Page

from qfdmd.models import HomePage


class Command(BaseCommand):
    help = "Migrate the current homepage to a new wagtail model"

    DEFAULT_HERO_SUBTITLE = (
        "Vous aider à <b>prolonger</b> la vie de vos objets, "
        "faire des <b>économies</b> et réduire vos déchets\u00a0!"
    )
    DEFAULT_HERO_SEARCH_LABEL = (
        "Pour quel objet ou déchet recherchez-vous "
        "des recommandations et des solutions\u00a0?"
    )

    def handle(self, *args, **options):
        if HomePage.objects.exists():
            self.stdout.write(
                self.style.WARNING("A HomePage already exists. Nothing to do.")
            )
            return

        homepage = Page.objects.get(depth=2).specific
        next_homepage = HomePage(
            title=homepage.title,
            seo_title=homepage.seo_title,
            body=homepage.body,
            search_description=homepage.search_description,
            hero_subtitle=self.DEFAULT_HERO_SUBTITLE,
            hero_search_label=self.DEFAULT_HERO_SEARCH_LABEL,
        )
        homepage.add_sibling(instance=next_homepage, pos="right")
        homepage.unpublish()
        r = homepage.save_revision()
        homepage.publish(r)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Page id={homepage.id} is now a HomePage. "
                "Edit it in the Wagtail admin to customise hero_title and icons."
            )
        )
