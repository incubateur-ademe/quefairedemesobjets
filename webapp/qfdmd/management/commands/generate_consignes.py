"""Run by every deploy (bin/post_deploy): give each live fiche its grid of
consignes, converted from its first row of cards. A no-op on a fiche that
already has one, see `generate_on_deploy`."""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmd.consignes_migration import generate_on_deploy
from qfdmd.models import ProduitPage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Génère la grille de consignes des fiches publiées qui n'en ont pas"

    def handle(self, *args, **options):
        failed = 0
        for page in ProduitPage.objects.live().order_by("pk"):
            try:
                with transaction.atomic():
                    result = generate_on_deploy(page)
            except Exception:
                # One broken fiche must not block the deploy: the others go
                # on, this one is retried by the next deploy.
                logger.exception("generate_consignes: fiche %s", page.pk)
                failed += 1
                result = "ERREUR, voir le log"
            self.stdout.write(f"{page.pk} {page.slug} : {result}")
        if failed:
            self.stderr.write(f"{failed} fiche(s) en erreur")
