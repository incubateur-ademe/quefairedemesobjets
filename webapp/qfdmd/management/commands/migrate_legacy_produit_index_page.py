# TODO: delete later. One-shot migration command; remove together with
# LegacyProduitIndexPage and its template once it has run in all environments.
from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmd.models import LegacyProduitIndexPage, ProduitIndexPage

# Fields carried over from the legacy page. Slug is intentionally excluded:
# it must stay unique while both pages coexist, and is swapped at the end.
# These are the fields shared by both the legacy and the new model; the draft
# revision (if any) carries them over too via the latest revision content.
COPIED_FIELDS = ("title", "body", "seo_title", "search_description")

TEMP_SLUG_SUFFIX = "-migration"


class Command(BaseCommand):
    help = (
        "Migrate the legacy ProduitIndexPage (Page-based) onto the new "
        "ContentPage-based ProduitIndexPage: copy its published content and any "
        "unpublished draft, move its children under the new page, delete the "
        "legacy page and restore the original slug."
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
        had_unpublished_changes = legacy.has_unpublished_changes

        # The meaningful content (notably body) lives on the latest revision when
        # the page has unpublished changes; the live fields can be empty. Prefer
        # the latest revision content, falling back to the live field values.
        latest_revision = legacy.latest_revision
        source = latest_revision.content if latest_revision is not None else {}

        def value_for(field):
            if field in source:
                return source[field]
            return getattr(legacy, field)

        # 1. Create the new page under the same parent with a temporary slug so
        #    both pages can coexist (slug must be unique among siblings). Build it
        #    from the live values first so the published version matches.
        new_page = ProduitIndexPage(
            slug=f"{original_slug}{TEMP_SLUG_SUFFIX}",
            live=legacy.live,
            **{field: getattr(legacy, field) for field in COPIED_FIELDS},
        )
        parent.add_child(instance=new_page)
        self.stdout.write(f"Created new ProduitIndexPage (id={new_page.pk}).")

        # 2. Save a revision carrying the draft content. When the legacy page had
        #    unpublished changes we keep it unpublished; otherwise we publish so
        #    the live version reflects the content.
        for field in COPIED_FIELDS:
            setattr(new_page, field, value_for(field))
        revision = new_page.save_revision(clean=False)
        if not had_unpublished_changes:
            revision.publish()
        self.stdout.write(
            f"Copied content (unpublished_changes={had_unpublished_changes})."
        )

        # 3. Move every child of the legacy page under the new page.
        children = list(legacy.get_children())
        for child in children:
            child.move(new_page, pos="last-child")
        self.stdout.write(f"Moved {len(children)} child page(s).")

        # 4. Delete the legacy page (now childless).
        legacy.refresh_from_db()
        legacy_id = legacy.pk
        legacy.delete()
        self.stdout.write(f"Deleted LegacyProduitIndexPage (id={legacy_id}).")

        # 5. Restore the original slug. Update the draft revision too so the
        #    editor and any future publish use the right slug, without clobbering
        #    the body we just copied.
        new_page = ProduitIndexPage.objects.get(pk=new_page.pk)
        new_page.slug = original_slug
        new_page.save()
        latest = new_page.latest_revision
        if latest is not None:
            latest.content["slug"] = original_slug
            latest.save(update_fields=["content"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Migration done: ProduitIndexPage (id={new_page.pk}) now at "
                f"slug '{original_slug}'."
            )
        )
