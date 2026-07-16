from types import SimpleNamespace

import pytest
from django.urls import reverse
from wagtail.models import Page

from qfdmd.legacy_migration import (
    MigrationError,
    migrate_produit,
    revert_produit_migration,
)
from qfdmd.models import (
    LEGACY_PRODUIT_INDEX_SLUG,
    Produit,
    ProduitIndexPage,
    ProduitPage,
    SearchTag,
)
from qfdmd.wagtail_hooks import (
    MigrateProduitsBulkAction,
    RevertProduitsMigrationBulkAction,
)
from unit_tests.qfdmd.qfdmod_factory import ProduitFactory, SynonymeFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def index_dechet():
    root_page = Page.objects.get(depth=1)
    page = ProduitIndexPage(title="Déchets", slug=LEGACY_PRODUIT_INDEX_SLUG)
    root_page.add_child(instance=page)
    page.save()
    return page


def test_migrate_puis_revert_restaure_l_etat_initial(index_dechet):
    produit = ProduitFactory(nom="Baignoire")
    synonyme = SynonymeFactory(produit=produit, nom="Sabot de bain")

    report = migrate_produit(produit, index_page=index_dechet)
    page_pk = report.page.pk
    synonyme.refresh_from_db()
    tag_pk = synonyme.legacy_imported_as_search_tag_id
    assert tag_pk is not None

    revert_produit_migration(produit)

    produit.refresh_from_db()
    synonyme.refresh_from_db()
    assert produit.legacy_imported_as_produit_page is None
    assert synonyme.legacy_imported_as_search_tag is None
    assert not ProduitPage.objects.filter(pk=page_pk).exists()
    # The SearchTag created by the migration was orphan: deleted.
    assert not SearchTag.objects.filter(pk=tag_pk).exists()
    # The produit is eligible for migration again.
    assert Produit.objects.to_migrate().filter(pk=produit.pk).exists()


def test_revert_conserve_les_search_tags_encore_utilises(index_dechet):
    produit = ProduitFactory(nom="Chaise")
    synonyme = SynonymeFactory(produit=produit, nom="Tabouret")
    migrate_produit(produit, index_page=index_dechet)
    synonyme.refresh_from_db()
    tag = synonyme.legacy_imported_as_search_tag

    # Another synonyme, manually imported, still references the tag.
    autre = SynonymeFactory(nom="Banc")
    autre.imported_as_search_tag = tag
    autre.save(update_fields=["imported_as_search_tag"])

    revert_produit_migration(produit)

    assert SearchTag.objects.filter(pk=tag.pk).exists()


def test_revert_refuse_un_produit_non_migre(index_dechet):
    produit = ProduitFactory(nom="Vélo")
    with pytest.raises(MigrationError):
        revert_produit_migration(produit)


def test_revert_refuse_une_page_non_migree_automatiquement(index_dechet):
    produit = ProduitFactory(nom="Table")
    page = ProduitPage(title="Table", slug="table")
    index_dechet.add_child(instance=page)
    page.save_revision().publish()
    produit.legacy_imported_as_produit_page = page
    produit.save(update_fields=["legacy_imported_as_produit_page"])

    with pytest.raises(MigrationError):
        revert_produit_migration(produit)


def test_migrate_refuse_un_produit_deja_migre(index_dechet):
    produit = ProduitFactory(nom="Fauteuil")
    migrate_produit(produit, index_page=index_dechet)
    produit.refresh_from_db()
    with pytest.raises(MigrationError):
        migrate_produit(produit, index_page=index_dechet)


def test_bulk_action_migrate_ignore_les_produits_non_eligibles(index_dechet):
    eligible = ProduitFactory(nom="Matelas")
    deja_migre = ProduitFactory(nom="Sommier")
    migrate_produit(deja_migre, index_page=index_dechet)
    deja_migre.refresh_from_db()

    instance = SimpleNamespace()
    migrated, _ = MigrateProduitsBulkAction.execute_action(
        [eligible, deja_migre], self=instance
    )

    eligible.refresh_from_db()
    assert migrated == 1
    assert eligible.legacy_imported_as_produit_page is not None
    assert len(instance.errors) == 1
    assert "Sommier" in instance.errors[0]


def test_bulk_action_revert_annule_la_migration(index_dechet):
    produit = ProduitFactory(nom="Armoire")
    migrate_produit(produit, index_page=index_dechet)
    produit.refresh_from_db()

    instance = SimpleNamespace()
    reverted, _ = RevertProduitsMigrationBulkAction.execute_action(
        [produit], self=instance
    )

    produit.refresh_from_db()
    assert reverted == 1
    assert instance.errors == []
    assert produit.legacy_imported_as_produit_page is None


def test_vue_migrate_affiche_une_confirmation_sur_get(admin_client, index_dechet):
    produit = ProduitFactory(nom="Baignoire")
    SynonymeFactory(produit=produit, nom="Sabot de bain")

    response = admin_client.get(reverse("migrate_single_produit", args=[produit.pk]))

    assert response.status_code == 200
    assert "admin/qfdmd/confirm_migrate_produit.html" in [
        t.name for t in response.templates
    ]
    content = response.content.decode()
    assert "Baignoire" in content
    assert "1" in str(response.context["nb_synonymes"])


def test_vue_revert_affiche_une_confirmation_sur_get(admin_client, index_dechet):
    produit = ProduitFactory(nom="Armoire")
    migrate_produit(produit, index_page=index_dechet)
    produit.refresh_from_db()

    response = admin_client.get(reverse("revert_single_produit", args=[produit.pk]))

    assert response.status_code == 200
    assert "admin/qfdmd/confirm_revert_produit.html" in [
        t.name for t in response.templates
    ]
    assert "Armoire" in response.content.decode()
