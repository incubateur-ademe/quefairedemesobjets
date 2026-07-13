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
)
from unit_tests.qfdmd.qfdmod_factory import (
    ProduitFactory,
    ProduitPageFactory,
    SynonymeFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def root_page():
    return Page.objects.get(depth=1)


@pytest.fixture
def index_dechet(root_page):
    page = ProduitIndexPage(title="Déchets", slug=LEGACY_PRODUIT_INDEX_SLUG)
    root_page.add_child(instance=page)
    page.save()
    return page


def test_migration_cree_la_page_et_copie_les_champs(index_dechet):
    produit = ProduitFactory(
        nom="Baignoire",
        code="BAI",
        qu_est_ce_que_j_en_fais="Texte legacy",
    )

    call_command("migrate_produits_legacy")

    produit.refresh_from_db()
    page = produit.legacy_imported_as_produit_page
    assert page is not None
    assert page.get_parent().pk == index_dechet.pk
    assert page.live is True
    assert page.title == "Baignoire"
    assert page.automatically_migrated_from_legacy_produit is True
    assert page.legacy_nom == "Baignoire"
    assert page.legacy_code == "BAI"
    assert page.legacy_qu_est_ce_que_j_en_fais == "Texte legacy"
    # The migrated produit leaves the migration queue.
    assert not Produit.objects.to_migrate().filter(pk=produit.pk).exists()


def test_migration_importe_uniquement_les_synonymes_non_migres(index_dechet):
    produit = ProduitFactory(nom="Chaise")
    to_migrate = SynonymeFactory(nom="Tabouret", produit=produit)
    already_migrated = SynonymeFactory(
        nom="Fauteuil",
        produit=produit,
        imported_as_search_tag=SearchTag.objects.create(name="Fauteuil"),
    )

    call_command("migrate_produits_legacy")

    to_migrate.refresh_from_db()
    already_migrated.refresh_from_db()
    assert to_migrate.legacy_imported_as_search_tag is not None
    assert to_migrate.legacy_imported_as_search_tag.name == "Tabouret"
    # Previously migrated synonymes must not be touched.
    assert already_migrated.legacy_imported_as_search_tag is None
    assert already_migrated.imported_as_search_tag.name == "Fauteuil"


def test_option_ids_limite_la_migration(index_dechet):
    p1 = ProduitFactory(nom="Un")
    p2 = ProduitFactory(nom="Deux")

    call_command("migrate_produits_legacy", ids=[p1.pk])

    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.legacy_imported_as_produit_page is not None
    assert p2.legacy_imported_as_produit_page is None


def test_dry_run_annule_les_ecritures(index_dechet):
    produit = ProduitFactory(nom="Vélo")

    call_command("migrate_produits_legacy", dry_run=True)

    produit.refresh_from_db()
    assert produit.legacy_imported_as_produit_page is None
    assert not ProduitPage.objects.filter(
        automatically_migrated_from_legacy_produit=True
    ).exists()


def test_collision_de_slug_suffixe_la_page(index_dechet):
    produit = ProduitFactory(nom="Table")
    # The command falls back to slugify(nom) when Produit.slug is empty.
    existing = ProduitPageFactory.build(title="Table", slug="table")
    index_dechet.add_child(instance=existing)
    existing.save()

    call_command("migrate_produits_legacy")

    produit.refresh_from_db()
    assert produit.legacy_imported_as_produit_page.slug == "table-2"


def test_produit_deja_redirige_est_exclu(index_dechet):
    produit = ProduitFactory(nom="Matelas")
    target = ProduitPageFactory.build(title="Matelas cible", slug="matelas-cible")
    index_dechet.add_child(instance=target)
    target.save()
    LegacyIntermediateProduitPage.objects.create(page=target, produit=produit)

    call_command("migrate_produits_legacy")

    produit.refresh_from_db()
    assert produit.legacy_imported_as_produit_page is None
    # No new page must be created for this produit.
    assert not ProduitPage.objects.filter(
        automatically_migrated_from_legacy_produit=True
    ).exists()


def test_migration_relancee_est_idempotente(index_dechet):
    ProduitFactory(nom="Gourde")

    call_command("migrate_produits_legacy")
    call_command("migrate_produits_legacy")

    assert (
        ProduitPage.objects.filter(
            automatically_migrated_from_legacy_produit=True
        ).count()
        == 1
    )


def test_erreur_sans_index_ni_homepage():
    HomePage.objects.all().delete()
    ProduitFactory(nom="Orphelin")

    with pytest.raises(CommandError):
        call_command("migrate_produits_legacy")
