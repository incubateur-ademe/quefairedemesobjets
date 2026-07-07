import json
import sys

from django.core.management.base import BaseCommand

from qfdmd.models import ProduitPage


class Command(BaseCommand):
    help = (
        "Export ProduitPage instances to the JSON fixture format consumed by "
        "recreate_produit_pages. Run against a DB where the page still exists "
        "(restored backup, staging) to recover a deleted page."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "slugs",
            nargs="+",
            help="Slugs of the ProduitPages to export.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Write JSON to this file instead of stdout.",
        )

    def handle(self, *args, **options):
        exported = []
        for slug in options["slugs"]:
            try:
                page = ProduitPage.objects.get(slug=slug)
            except ProduitPage.DoesNotExist:
                self.stderr.write(f"ProduitPage with slug='{slug}' not found.")
                sys.exit(1)
            except ProduitPage.MultipleObjectsReturned:
                self.stderr.write(
                    f"Multiple ProduitPages with slug='{slug}', export by hand."
                )
                sys.exit(1)
            exported.append((page, self._export_page(page)))
            self.stderr.write(f"Exported '{page.title}' (id={page.pk})")

        # Sort parents before children (Wagtail materialized path) and, when a
        # page's parent is part of this export, reference it by _key so the
        # fixture replays on a DB where the original page ids no longer exist.
        exported.sort(key=lambda item: item[0].path)
        keys = {page_def["key"] for _, page_def in exported}
        pages = []
        for _, page_def in exported:
            parent_slug = page_def["parent_page_lookup"].get("slug")
            if parent_slug in keys:
                page_def["parent_page_lookup"] = {"_key": parent_slug}
            pages.append(page_def)

        fixture = {
            "description": "Exported by export_produit_pages",
            "pages": pages,
        }
        output = json.dumps(fixture, indent=2, ensure_ascii=False)

        if options["output"]:
            with open(options["output"], "w") as f:
                f.write(output)
            self.stderr.write(f"Wrote {options['output']}")
        else:
            self.stdout.write(output)

    def _export_page(self, page):
        parent = page.get_parent()
        return {
            "key": page.slug,
            # ponytail: id wins in recreate's lookup; slug kept as a
            # human-readable hint and cross-env fallback
            "parent_page_lookup": {"id": parent.pk, "slug": parent.slug},
            "page_type": "produitpage",
            "title": page.title,
            "slug": page.slug,
            "seo_title": page.seo_title,
            "search_description": page.search_description,
            "live": page.live,
            "show_in_menus": page.show_in_menus,
            "genre": page.genre,
            "nombre": page.nombre,
            "est_famille": page.est_famille,
            "titre_phrase": page.titre_phrase,
            "usage_unique": page.usage_unique,
            "ab_test_carte_default_view": page.ab_test_carte_default_view,
            "migree_depuis_synonymes_legacy": page.migree_depuis_synonymes_legacy,
            "commentaire": page.commentaire,
            "go_live_at": page.go_live_at.isoformat() if page.go_live_at else None,
            "expire_at": page.expire_at.isoformat() if page.expire_at else None,
            "legacy_produit_noms": sorted(
                rel.produit.nom for rel in page.legacy_produit.all()
            ),
            "legacy_synonyme_noms": sorted(
                rel.synonyme.nom for rel in page.legacy_synonymes.all()
            ),
            "legacy_synonyme_exclusion_noms": sorted(
                rel.synonyme.nom for rel in page.legacy_synonymes_to_exclude.all()
            ),
            "tag_names": sorted(t.name for t in page.tags.all()),
            "search_tag_names": sorted(t.name for t in page.search_tags.all()),
            "sous_categorie_objet_codes": sorted(
                sc.code for sc in page.sous_categorie_objet.all()
            ),
            "infotri": list(page.infotri.raw_data) if page.infotri else [],
            "body": list(page.body.raw_data) if page.body else [],
        }
