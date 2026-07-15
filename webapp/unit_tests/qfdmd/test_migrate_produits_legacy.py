"""Tests de la commande ``migrate_produits_legacy``.

Ces tests s'appuient sur ``fixtures/produits_legacy.json``, un extrait réel
de la base de dev (8 produits et leurs 26 synonymes), qui embarque les
aspérités des vraies données : slugs accentués (``Acétone``), slug vide
(``Aimant``), code vide, parenthèses dans le nom, etc.
"""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from wagtail.models import Page

from qfdmd.models import (
    LEGACY_PRODUIT_INDEX_SLUG,
    HomePage,
    LegacyIntermediateProduitPage,
    Produit,
    ProduitIndexPage,
    ProduitPage,
    SearchTag,
    Synonyme,
)
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory

pytestmark = pytest.mark.django_db

FIXTURE_PRODUITS_LEGACY = str(
    Path(__file__).parent / "fixtures" / "produits_legacy.json"
)

# Extrait réel de la base de dev — voir fixtures/produits_legacy.json.
ACETONE_PK = 3  # slug accentué "Acétone", code ADEME_DDS
AMIANTE_PK = 10  # 5 synonymes
AIMANT_PK = 491  # slug et code vides
ANTIVOL_PK = 16
FIXTURE_PRODUITS_COUNT = 8


@pytest.fixture
def produits_legacy():
    call_command("loaddata", FIXTURE_PRODUITS_LEGACY)


@pytest.fixture
def root_page():
    return Page.objects.get(depth=1)


@pytest.fixture
def index_dechet(root_page):
    page = ProduitIndexPage(title="Déchets", slug=LEGACY_PRODUIT_INDEX_SLUG)
    root_page.add_child(instance=page)
    page.save()
    return page


def test_la_fixture_alimente_la_file_de_migration(produits_legacy):
    assert Produit.objects.to_migrate().count() == FIXTURE_PRODUITS_COUNT
    assert (
        Synonyme.objects.filter(legacy_imported_as_search_tag__isnull=True).count()
        == 26
    )


def test_migration_cree_la_page_et_copie_les_champs(produits_legacy, index_dechet):
    produit = Produit.objects.get(pk=ACETONE_PK)

    call_command("migrate_produits_legacy", ids=[ACETONE_PK])

    produit.refresh_from_db()
    page = produit.legacy_imported_as_produit_page
    assert page is not None
    assert page.get_parent().pk == index_dechet.pk
    assert page.live is True
    assert page.title == "Acétone"
    # Le slug legacy "Acétone" (accentué) est normalisé par slugify.
    assert page.slug == "acetone"
    assert page.automatically_migrated_from_legacy_produit is True
    assert page.legacy_nom == "Acétone"
    assert page.legacy_code == "ADEME_DDS"
    assert page.legacy_qu_est_ce_que_j_en_fais == produit.qu_est_ce_que_j_en_fais
    assert page.legacy_qu_est_ce_que_j_en_fais != ""
    # Le produit migré quitte la file de migration.
    assert not Produit.objects.to_migrate().filter(pk=produit.pk).exists()


def test_slug_produit_vide_retombe_sur_le_nom(produits_legacy, index_dechet):
    produit = Produit.objects.get(pk=AIMANT_PK)
    assert produit.slug == ""
    assert produit.code == ""

    call_command("migrate_produits_legacy", ids=[AIMANT_PK])

    produit.refresh_from_db()
    assert produit.legacy_imported_as_produit_page.slug == "aimant"


def test_migration_importe_uniquement_les_synonymes_non_migres(
    produits_legacy, index_dechet
):
    produit = Produit.objects.get(pk=AMIANTE_PK)
    deja_migre = produit.synonymes.get(nom="Fibro-ciment")
    deja_migre.imported_as_search_tag = SearchTag.objects.create(name="Fibro-ciment")
    deja_migre.save(update_fields=["imported_as_search_tag"])

    call_command("migrate_produits_legacy", ids=[AMIANTE_PK])

    deja_migre.refresh_from_db()
    a_migrer = produit.synonymes.exclude(pk=deja_migre.pk)
    assert a_migrer.count() == 4
    for synonyme in a_migrer:
        assert synonyme.legacy_imported_as_search_tag is not None
        assert synonyme.legacy_imported_as_search_tag.name == synonyme.nom
    # Les synonymes déjà migrés ne doivent pas être retouchés.
    assert deja_migre.legacy_imported_as_search_tag is None
    assert deja_migre.imported_as_search_tag.name == "Fibro-ciment"


def test_option_ids_limite_la_migration(produits_legacy, index_dechet):
    call_command("migrate_produits_legacy", ids=[ACETONE_PK])

    acetone = Produit.objects.get(pk=ACETONE_PK)
    aimant = Produit.objects.get(pk=AIMANT_PK)
    assert acetone.legacy_imported_as_produit_page is not None
    assert aimant.legacy_imported_as_produit_page is None


def test_dry_run_annule_les_ecritures(produits_legacy, index_dechet):
    call_command("migrate_produits_legacy", dry_run=True)

    assert not Produit.objects.filter(
        legacy_imported_as_produit_page__isnull=False
    ).exists()
    assert not ProduitPage.objects.filter(
        automatically_migrated_from_legacy_produit=True
    ).exists()
    assert not Synonyme.objects.filter(
        legacy_imported_as_search_tag__isnull=False
    ).exists()


def test_collision_de_slug_suffixe_la_page(produits_legacy, index_dechet):
    existing = ProduitPageFactory.build(title="Acétone", slug="acetone")
    index_dechet.add_child(instance=existing)
    existing.save()

    call_command("migrate_produits_legacy", ids=[ACETONE_PK])

    produit = Produit.objects.get(pk=ACETONE_PK)
    assert produit.legacy_imported_as_produit_page.slug == "acetone-2"


def test_produit_deja_redirige_est_exclu(produits_legacy, index_dechet):
    produit = Produit.objects.get(pk=ANTIVOL_PK)
    target = ProduitPageFactory.build(title="Antivol cible", slug="antivol-cible")
    index_dechet.add_child(instance=target)
    target.save()
    LegacyIntermediateProduitPage.objects.create(page=target, produit=produit)

    call_command("migrate_produits_legacy")

    produit.refresh_from_db()
    assert produit.legacy_imported_as_produit_page is None
    assert not ProduitPage.objects.filter(
        automatically_migrated_from_legacy_produit=True,
        legacy_nom="Antivol",
    ).exists()


def test_migration_relancee_est_idempotente(produits_legacy, index_dechet):
    call_command("migrate_produits_legacy")
    call_command("migrate_produits_legacy")

    assert (
        ProduitPage.objects.filter(
            automatically_migrated_from_legacy_produit=True
        ).count()
        == FIXTURE_PRODUITS_COUNT
    )
    assert Produit.objects.to_migrate().count() == 0


def test_erreur_sans_index_ni_homepage(produits_legacy):
    HomePage.objects.all().delete()

    with pytest.raises(CommandError):
        call_command("migrate_produits_legacy")
