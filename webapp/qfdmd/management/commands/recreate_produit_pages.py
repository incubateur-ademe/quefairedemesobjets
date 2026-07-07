import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from taggit.models import Tag
from wagtail.models import Page

from qfdmd.models import (
    LegacyIntermediateProduitPage,
    LegacyIntermediateProduitPageSynonymeExclusion,
    LegacyIntermediateSynonymePage,
    Produit,
    ProduitPage,
    SearchTag,
    Synonyme,
)
from qfdmo.models import SousCategorieObjet


class Command(BaseCommand):
    help = "Recreate ProduitPage instances from a JSON fixture using add_child()."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixture",
            type=str,
            help="Path to the JSON fixture file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and show what would be created without saving.",
        )
        parser.add_argument(
            "--parent-page-id",
            type=int,
            default=None,
            help="Override the parent page ID for the first page in the fixture.",
        )

    def handle(self, *args, **options):
        fixture_path = Path(options["fixture"])
        dry_run = options["dry_run"]
        parent_page_id_override = options["parent_page_id"]

        if not fixture_path.exists():
            self.stderr.write(f"Fixture file not found: {fixture_path}")
            sys.exit(1)

        with open(fixture_path) as f:
            data = json.load(f)

        pages = data.get("pages", [])
        if not pages:
            self.stderr.write("No pages found in fixture.")
            return

        if parent_page_id_override is not None and pages:
            pages[0]["parent_page_lookup"] = {"id": parent_page_id_override}
            self.stdout.write(
                f"Overriding first page parent to id={parent_page_id_override}"
            )

        created_pages = {}
        for i, page_def in enumerate(pages):
            self.stdout.write(f"\n--- Page {i + 1}/{len(pages)} ---")
            created = self._create_page(page_def, created_pages, dry_run)
            if created:
                created_pages[page_def.get("key", page_def["slug"])] = created

        if created_pages:
            self.stdout.write(
                self.style.SUCCESS(f"\nCreated {len(created_pages)} page(s).")
            )

    def _find_parent(self, page_def, created_pages):
        parent_lookup = page_def.get("parent_page_lookup")
        if not parent_lookup:
            self.stderr.write("  Missing parent_page_lookup.")
            return None

        parent_key = parent_lookup.get("_key")
        if parent_key:
            parent = created_pages.get(parent_key)
            if parent:
                return parent
            self.stderr.write(
                f"  Parent key '{parent_key}' not found in created pages "
                "(must be defined before child)."
            )
            return None

        parent_id = parent_lookup.get("id")
        parent_slug = parent_lookup.get("slug")
        if parent_id:
            try:
                return Page.objects.get(id=parent_id).specific
            except Page.DoesNotExist:
                if not parent_slug:
                    self.stderr.write(f"  Parent page with id={parent_id} not found.")
                    return None
                self.stdout.write(
                    f"  Parent page with id={parent_id} not found, "
                    f"falling back to slug='{parent_slug}'."
                )

        if parent_slug:
            try:
                return Page.objects.get(slug=parent_slug).specific
            except Page.DoesNotExist:
                self.stderr.write(f"  Parent page with slug='{parent_slug}' not found.")
                return None
            except Page.MultipleObjectsReturned:
                self.stderr.write(
                    f"  Multiple pages found with slug='{parent_slug}'. Use id instead."
                )
                return None

        self.stderr.write("  parent_page_lookup must contain one of: id, slug, _key.")
        return None

    def _create_page(self, page_def, created_pages, dry_run):
        parent = self._find_parent(page_def, created_pages)
        if parent is None:
            return None

        page_type = page_def.get("page_type", "produitpage")
        if page_type != "produitpage":
            self.stderr.write(f"  Unsupported page_type: {page_type}")
            return None

        title = page_def.get("title", "")
        slug_value = page_def.get("slug", "")
        self.stdout.write(
            f"  Creating '{title}' under '{parent.title}' (parent id={parent.pk})"
        )

        if dry_run:
            self._dry_run_report(page_def)
            return None

        page = ProduitPage(
            title=title,
            slug=slug_value,
            live=page_def.get("live", True),
            show_in_menus=page_def.get("show_in_menus", False),
            seo_title=page_def.get("seo_title", ""),
            search_description=page_def.get("search_description", ""),
            genre=page_def.get("genre", ""),
            nombre=page_def.get("nombre"),
            est_famille=page_def.get("est_famille", False),
            titre_phrase=page_def.get("titre_phrase", ""),
            usage_unique=page_def.get("usage_unique", False),
            ab_test_carte_default_view=page_def.get(
                "ab_test_carte_default_view", False
            ),
            migree_depuis_synonymes_legacy=page_def.get(
                "migree_depuis_synonymes_legacy", False
            ),
            commentaire=page_def.get("commentaire", ""),
        )

        go_live_at = page_def.get("go_live_at")
        if go_live_at:
            page.go_live_at = parse_datetime(go_live_at)
        expire_at = page_def.get("expire_at")
        if expire_at:
            page.expire_at = parse_datetime(expire_at)

        parent.add_child(instance=page)

        body = page_def.get("body")
        if body is not None:
            page.body = body

        infotri = page_def.get("infotri")
        if infotri is not None:
            page.infotri = infotri

        page.save()

        self._attach_tags(page, page_def)
        self._attach_search_tags(page, page_def)
        self._attach_sous_categories(page, page_def)
        self._attach_legacy_redirects(page, page_def)

        revision = page.save_revision()
        if page_def.get("live", True):
            revision.publish()

        self.stdout.write(
            self.style.SUCCESS(f"  Created page id={page.pk}, slug='{page.slug}'")
        )

        return page

    def _attach_tags(self, page, page_def):
        tag_names = page_def.get("tag_names", [])
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            page.tags.add(tag)
            if created:
                self.stdout.write(f"    Created tag: '{name}'")

        tag_slugs = page_def.get("tag_slugs", [])
        for slug in tag_slugs:
            try:
                tag = Tag.objects.get(slug=slug)
                page.tags.add(tag)
            except Tag.DoesNotExist:
                self.stderr.write(f"    Tag with slug='{slug}' not found, skipping.")

    def _attach_search_tags(self, page, page_def):
        search_tag_names = page_def.get("search_tag_names", [])
        for name in search_tag_names:
            tag, created = SearchTag.objects.get_or_create(name=name)
            page.search_tags.add(tag)
            if created:
                self.stdout.write(f"    Created search tag: '{name}'")

    def _attach_sous_categories(self, page, page_def):
        codes = page_def.get("sous_categorie_objet_codes", [])
        for code in codes:
            try:
                sc = SousCategorieObjet.objects.get(code=code)
                page.sous_categorie_objet.add(sc)
            except SousCategorieObjet.DoesNotExist:
                self.stderr.write(
                    f"    SousCategorieObjet with code='{code}' not found, skipping."
                )

    def _attach_legacy_redirects(self, page, page_def):
        """Recreate the legacy Django → Wagtail redirect relations.

        The intermediate rows are deleted in cascade with the page, but the
        Produit/Synonyme objects survive, so they are looked up by nom.
        """
        for nom in page_def.get("legacy_produit_noms", []):
            try:
                produit = Produit.objects.get(nom=nom)
                LegacyIntermediateProduitPage.objects.create(page=page, produit=produit)
            except Produit.DoesNotExist:
                self.stderr.write(f"    Produit '{nom}' not found, skipping.")
            except Exception as e:
                self.stderr.write(f"    Could not redirect produit '{nom}': {e}")

        for nom in page_def.get("legacy_synonyme_noms", []):
            try:
                synonyme = Synonyme.objects.get(nom=nom)
                LegacyIntermediateSynonymePage.objects.create(
                    page=page, synonyme=synonyme
                )
            except Synonyme.DoesNotExist:
                self.stderr.write(f"    Synonyme '{nom}' not found, skipping.")
            except Exception as e:
                self.stderr.write(f"    Could not redirect synonyme '{nom}': {e}")

        for nom in page_def.get("legacy_synonyme_exclusion_noms", []):
            try:
                synonyme = Synonyme.objects.get(nom=nom)
                LegacyIntermediateProduitPageSynonymeExclusion.objects.create(
                    page=page, synonyme=synonyme
                )
            except Synonyme.DoesNotExist:
                self.stderr.write(
                    f"    Synonyme (exclusion) '{nom}' not found, skipping."
                )
            except Exception as e:
                self.stderr.write(f"    Could not exclude synonyme '{nom}': {e}")

    def _dry_run_report(self, page_def):
        tag_names = page_def.get("tag_names", [])
        search_tag_names = page_def.get("search_tag_names", [])
        sc_codes = page_def.get("sous_categorie_objet_codes", [])

        self.stdout.write(f"    genre: {page_def.get('genre', '')}")
        self.stdout.write(f"    nombre: {page_def.get('nombre')}")
        self.stdout.write(f"    est_famille: {page_def.get('est_famille', False)}")
        self.stdout.write(f"    titre_phrase: {page_def.get('titre_phrase', '')}")
        self.stdout.write(f"    usage_unique: {page_def.get('usage_unique', False)}")
        self.stdout.write(
            f"    ab_test_carte_default_view: "
            f"{page_def.get('ab_test_carte_default_view', False)}"
        )
        self.stdout.write(
            f"    migree_depuis_synonymes_legacy: "
            f"{page_def.get('migree_depuis_synonymes_legacy', False)}"
        )
        self.stdout.write(f"    body blocks: {len(page_def.get('body', []))}")
        self.stdout.write(f"    infotri blocks: {len(page_def.get('infotri', []))}")
        self.stdout.write(f"    tag_names: {tag_names}")
        self.stdout.write(f"    search_tag_names: {search_tag_names}")
        self.stdout.write(f"    sous_categorie_objet_codes: {sc_codes}")
        self.stdout.write(f"    go_live_at: {page_def.get('go_live_at')}")
        self.stdout.write(f"    expire_at: {page_def.get('expire_at')}")
        self.stdout.write(
            f"    legacy_produit_noms: {page_def.get('legacy_produit_noms', [])}"
        )
        self.stdout.write(
            f"    legacy_synonyme_noms: {page_def.get('legacy_synonyme_noms', [])}"
        )
        self.stdout.write(
            f"    legacy_synonyme_exclusion_noms: "
            f"{page_def.get('legacy_synonyme_exclusion_noms', [])}"
        )
        self.stdout.write("  [DRY RUN] Would create page (not saved).")
