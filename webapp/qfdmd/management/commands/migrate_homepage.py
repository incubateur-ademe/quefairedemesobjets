import itertools
from io import BytesIO
from pathlib import Path

import willow
from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image
from wagtail.models import Page, Site

from qfdmd.models import HomePage

ICONS_DIR = "TEMPORARY_ICONS_TO_DOWNLOAD_FOR_NEW_HOMEPAGE"


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
        if not HomePage.objects.exists():
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

            # Move children from old homepage to new homepage
            for child in homepage.get_children():
                child.move(next_homepage, pos="last-child")

            # Update the site root page
            site = Site.objects.first()
            if site:
                site.root_page = next_homepage
                site.save()
            else:
                self.stdout.write(
                    self.style.WARNING("No Wagtail site found. root_page not updated.")
                )

            # Unpublish old homepage
            homepage.unpublish()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. Page id={next_homepage.id} is now the HomePage. "
                    "Edit it in the Wagtail admin to customise hero_title and icons."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("HomePage already exists, skipping page creation.")
            )
            next_homepage = HomePage.objects.first()

        self.import_icons(next_homepage)

    def import_icons(self, homepage):
        icons_dir = Path(settings.BASE_DIR) / ICONS_DIR
        if not icons_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Icons directory not found: {icons_dir}")
            )
            return

        homepage.icons = []

        MIN_ICONS = 53
        paths = sorted(p for p in icons_dir.iterdir() if not p.is_dir())
        # Repeat the list until we reach the minimum count
        imported = 0
        for path in itertools.islice(
            itertools.cycle(paths), max(MIN_ICONS, len(paths))
        ):
            img_bytes = path.read_bytes()
            with path.open(mode="rb") as f:
                img_file = ImageFile(BytesIO(img_bytes), name=path.name)
                im = willow.Image.open(f)
                width, height = im.get_size()
                img_obj = Image(
                    title=path.stem,
                    file=img_file,
                    width=width,
                    height=height,
                )
                img_obj.save()
            homepage.icons.append(
                ("image", {"image": img_obj, "decorative": True, "alt_text": ""})
            )
            imported += 1

        homepage.save_revision().publish()
        self.stdout.write(self.style.SUCCESS(f"Imported {imported} icons."))
