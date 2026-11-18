"""Run by every deploy (bin/post_deploy): give each live fiche its grid of
consignes, converted from its first row of cards. A no-op on a fiche that
already has one, see `generate_on_deploy`.

TODO: remove once the consignes grid is live in production."""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from qfdmd.consignes_migration import apply_plan, plan_conversion
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
            except Exception as e:
                # One broken fiche must not block the deploy: the others go
                # on, this one is retried by the next deploy.
                logger.exception("generate_consignes: fiche %s", page.pk)
                failed += 1
                result = f"ERREUR : {e!r}"
            self.stdout.write(f"{page.pk} {page.slug} : {result}")
        if failed:
            self.stderr.write(f"{failed} fiche(s) en erreur")


def generate_on_deploy(page: ProduitPage) -> str:
    """Give a live fiche its grid, once. Returns what was done, for the log.

    A fiche whose live version or pending draft already holds a grid is left
    alone, so every deploy can run this. A clean conversion is published; one
    with cards left behind becomes a draft for an editor to finish. An
    editor's pending draft is never lost: publishing would bury it under the
    new revision, so it is converted the same way and saved back on top.
    """
    draft = (
        page.get_latest_revision_as_object() if page.has_unpublished_changes else None
    )
    if _has_grid(page) or (draft and _has_grid(draft)):
        return "déjà une grille"

    plan = plan_conversion(page)
    if not plan.consignes:
        return "rien à convertir"
    if plan.unresolved:
        base = draft or page
        written = apply_plan(base, plan_conversion(base) if draft else plan)
        return (
            f"brouillon, {written} consignes, {len(plan.unresolved)} cartes à reprendre"
        )

    apply_plan(page, plan, publish=True)
    if draft:
        draft_plan = plan_conversion(draft)
        if not apply_plan(draft, draft_plan):
            draft.save_revision()  # unchanged, but on top again
    return f"publiée, {len(plan.consignes)} consignes" + (
        ", brouillon en cours converti aussi" if draft else ""
    )


def _has_grid(page: ProduitPage) -> bool:
    # The raw data, not `page.body` itself: iterating binds the blocks, and
    # get_prep_value() then re-serialises the cards in a shape the parsing
    # of first_row_of_cards() does not read.
    return any(block["type"] == "consignes" for block in page.body.get_prep_value())
