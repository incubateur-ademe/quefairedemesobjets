"""
Fix duplicate MainMenu records created by sites_conformes on each deploy.

sites_conformes may create a new MainMenu for the default site on every deploy,
leaving multiple rows that violate wagtailmenus' OneToOne constraint and crash
every page with:

    get() returned more than one MainMenu -- it returned 2!

Run after each migrate (via post_migrate signal) to keep at most one MainMenu
per site, preferring the existing one and discarding duplicates.
"""

import logging

from django.core.management.base import BaseCommand
from wagtail.models import Site
from wagtailmenus.models.menus import MainMenu

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Remove duplicate MainMenu records, keeping one per site"

    def handle(self, **options):
        fixed = 0
        for site in Site.objects.all():
            menus = list(MainMenu.objects.filter(site=site).order_by("pk"))
            if len(menus) <= 1:
                continue
            # Keep the first (oldest) MainMenu, delete the rest
            keep, *duplicates = menus
            for dup in duplicates:
                dup.delete()
                logger.info(
                    "Removed duplicate MainMenu pk=%s for site=%s (kept pk=%s)",
                    dup.pk,
                    site.hostname,
                    keep.pk,
                )
                fixed += 1

        if fixed:
            self.stdout.write(
                self.style.SUCCESS(f"Removed {fixed} duplicate MainMenu record(s)")
            )
        else:
            self.stdout.write(self.style.SUCCESS("No duplicate MainMenu records found"))
