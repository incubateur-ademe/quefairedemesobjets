from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from wagtail.models import Page

from qfdmd.models import HomePage


class Command(BaseCommand):
    help = (
        "Migrate the current depth=2 Wagtail page to the HomePage content type. "
        "Populates hero_title, hero_subtitle and hero_search_label with the "
        "default values that were previously hardcoded in the template."
    )

    DEFAULT_HERO_SUBTITLE = (
        "Vous aider à <b>prolonger</b> la vie de vos objets, "
        "faire des <b>économies</b> et réduire vos déchets\u00a0!"
    )
    DEFAULT_HERO_SEARCH_LABEL = (
        "Pour quel objet ou déchet recherchez-vous "
        "des recommandations et des solutions\u00a0?"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be done without making any changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        try:
            page = Page.objects.get(depth=2)
        except Page.DoesNotExist:
            self.stderr.write(self.style.ERROR("No page found at depth=2."))
            return
        except Page.MultipleObjectsReturned:
            self.stderr.write(
                self.style.ERROR(
                    "Multiple pages found at depth=2. "
                    "Cannot determine which one is the homepage."
                )
            )
            return

        if isinstance(page.specific, HomePage):
            self.stdout.write(
                self.style.WARNING(
                    f'Page "{page.title}" (id={page.id}) is already a HomePage. '
                    "Nothing to do."
                )
            )
            return

        homepage_ct = ContentType.objects.get_for_model(HomePage)

        self.stdout.write(
            f'Migrating page "{page.title}" (id={page.id}) '
            f"from content_type={page.content_type} "
            f"to HomePage (content_type_id={homepage_ct.id})."
        )
        self.stdout.write(f"  hero_subtitle  → {self.DEFAULT_HERO_SUBTITLE!r}")
        self.stdout.write(f"  hero_search_label → {self.DEFAULT_HERO_SEARCH_LABEL!r}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: no changes written."))
            return

        # Update the content type on the base Page row
        Page.objects.filter(pk=page.pk).update(content_type=homepage_ct)

        # Create the HomePage-specific row (ORM insert, no save_revision needed
        # for a content-type migration)
        HomePage.objects.create(
            page_ptr_id=page.pk,
            hero_title="",
            hero_subtitle=self.DEFAULT_HERO_SUBTITLE,
            hero_search_label=self.DEFAULT_HERO_SEARCH_LABEL,
            icons="[]",
            body="[]",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Page id={page.id} is now a HomePage. "
                "Edit it in the Wagtail admin to customise hero_title and icons."
            )
        )
