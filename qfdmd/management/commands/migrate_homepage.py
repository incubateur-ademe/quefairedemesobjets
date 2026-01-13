from django.core.management.base import BaseCommand
from wagtail.models import Page, Site


class Command(BaseCommand):
    help = "Move page 344 to root level, migrate children from page 2 to page 344, and update site root page"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command without making any changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get the pages and site
        try:
            root_page = Page.objects.get(id=1)
            page_2 = Page.objects.get(id=2)
            page_344 = Page.objects.get(id=344)
            site = Site.objects.get(id=1)
        except (Page.DoesNotExist, Site.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            return

        # Display current state
        self.stdout.write(self.style.SUCCESS("\n=== Current State ==="))
        self.stdout.write(f"Site: {site.site_name}")
        self.stdout.write(f"  - Hostname: {site.hostname}")
        self.stdout.write(
            f"  - Current root page: {site.root_page.title} (id={site.root_page.id})"
        )

        self.stdout.write(f"\nPage 2: {page_2.title}")
        self.stdout.write(f"  - Depth: {page_2.depth}")
        self.stdout.write(f"  - Parent: {page_2.get_parent().title}")
        self.stdout.write(f"  - Children count: {page_2.get_children().count()}")
        self.stdout.write(f"  - Live status: {page_2.live}")

        self.stdout.write(f"\nPage 344: {page_344.title}")
        self.stdout.write(f"  - Depth: {page_344.depth}")
        self.stdout.write(f"  - Parent: {page_344.get_parent().title}")
        self.stdout.write(f"  - Children count: {page_344.get_children().count()}")
        self.stdout.write(f"  - Live status: {page_344.live}")

        # Step 1: Move page 344 to root level (as sibling of page 2)
        self.stdout.write(
            self.style.SUCCESS("\n=== Step 1: Moving page 344 to root level ===")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY RUN] Would move page 344 to root level")
            )
        else:
            page_344.move(root_page, pos="last-child")
            page_344.refresh_from_db()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Page 344 moved to root level (depth={page_344.depth})"
                )
            )

        # Step 2: Move all children from page 2 to page 344
        self.stdout.write(
            self.style.SUCCESS(
                "\n=== Step 2: Moving children from page 2 to page 344 ==="
            )
        )

        children = page_2.get_children()
        children_count = children.count()

        if children_count == 0:
            self.stdout.write(self.style.WARNING("No children to move from page 2"))
        else:
            self.stdout.write(f"Found {children_count} children to move:")

            for i, child in enumerate(children, 1):
                self.stdout.write(f"  {i}. {child.title} (id={child.id})")

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING("     [DRY RUN] Would move to page 344")
                    )
                else:
                    child.move(page_344, pos="last-child")
                    self.stdout.write(self.style.SUCCESS("     ✓ Moved to page 344"))

        # Step 3: Update site root page to page 344
        self.stdout.write(
            self.style.SUCCESS("\n=== Step 3: Updating site root page to page 344 ===")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would update site root page from '{site.root_page.title}' (id={site.root_page.id}) to '{page_344.title}' (id=344)"
                )
            )
        else:
            site.root_page = page_344
            site.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Site root page updated to '{page_344.title}' (id=344)"
                )
            )

        # Step 4: Publish page 344
        self.stdout.write(self.style.SUCCESS("\n=== Step 4: Publishing page 344 ==="))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would publish page 344: '{page_344.title}' (currently live={page_344.live})"
                )
            )
        else:
            if not page_344.live:
                page_344.specific.save_revision().publish()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Page 344 '{page_344.title}' has been published"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Page 344 '{page_344.title}' is already published"
                    )
                )

        # Step 5: Unpublish page 2
        self.stdout.write(self.style.SUCCESS("\n=== Step 5: Unpublishing page 2 ==="))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would unpublish page 2: '{page_2.title}' (currently live={page_2.live})"
                )
            )
        else:
            if page_2.live:
                page_2.unpublish()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Page 2 '{page_2.title}' has been unpublished"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Page 2 '{page_2.title}' is already unpublished"
                    )
                )

        # Display final state
        self.stdout.write(self.style.SUCCESS("\n=== Final State ==="))

        page_2.refresh_from_db()
        page_344.refresh_from_db()
        site.refresh_from_db()

        self.stdout.write(f"Site: {site.site_name}")
        self.stdout.write(
            f"  - Root page: {site.root_page.title} (id={site.root_page.id})"
        )

        self.stdout.write(f"\nPage 2: {page_2.title}")
        self.stdout.write(f"  - Children count: {page_2.get_children().count()}")
        self.stdout.write(f"  - Live status: {page_2.live}")

        self.stdout.write(f"\nPage 344: {page_344.title}")
        self.stdout.write(f"  - Depth: {page_344.depth}")
        self.stdout.write(f"  - Parent: {page_344.get_parent().title}")
        self.stdout.write(f"  - Children count: {page_344.get_children().count()}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n✓ DRY RUN completed - no changes were made")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ Migration completed successfully!")
            )
