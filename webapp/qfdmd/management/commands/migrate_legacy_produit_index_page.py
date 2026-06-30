from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmd.models import LegacyProduitIndexPage, ProduitIndexPage

# Fields carried over from the legacy page. Slug is intentionally excluded:
# it must stay unique while both pages coexist, and is swapped at the end.
COPIED_FIELDS = ("title", "body", "seo_title", "search_description")

TEMP_SLUG_SUFFIX = "-migration"


class Command(BaseCommand):
    help = (
        "Migrate the legacy ProduitIndexPage (Page-based) onto the new "
        "ContentPage-based ProduitIndexPage: copy its content, move its children "
        "under the new page, delete the legacy page and restore the original slug."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        legacy = LegacyProduitIndexPage.objects.first()
        if legacy is None:
            self.stdout.write("No LegacyProduitIndexPage found, nothing to migrate.")
            return

        # Safe guard: if a new ProduitIndexPage already exists, the migration has
        # already run (or is mid-flight). Don't create a duplicate.
        if ProduitIndexPage.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "A ProduitIndexPage already exists, migration already done. "
                    "Aborting to avoid creating a duplicate."
                )
            )
            return

        original_slug = legacy.slug
        parent = legacy.get_parent()

        # 1. Create the new page under the same parent with a temporary slug so
        #    both pages can coexist (slug must be unique among siblings).
        new_page = ProduitIndexPage(
            slug=f"{original_slug}{TEMP_SLUG_SUFFIX}",
            **{field: getattr(legacy, field) for field in COPIED_FIELDS},
        )
        parent.add_child(instance=new_page)
        self.stdout.write(f"Created new ProduitIndexPage (id={new_page.pk}).")

        # 2. Move every child of the legacy page under the new page.
        children = list(legacy.get_children())
        for child in children:
            child.move(new_page, pos="last-child")
        self.stdout.write(f"Moved {len(children)} child page(s).")

        # 3. Delete the legacy page (now childless).
        legacy.refresh_from_db()
        legacy_id = legacy.pk
        legacy.delete()
        self.stdout.write(f"Deleted LegacyProduitIndexPage (id={legacy_id}).")

        # 4. Restore the original slug on the new page.
        new_page.refresh_from_db()
        new_page.slug = original_slug
        new_page.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Migration done: ProduitIndexPage (id={new_page.pk}) now at "
                f"slug '{original_slug}'."
            )
        )
