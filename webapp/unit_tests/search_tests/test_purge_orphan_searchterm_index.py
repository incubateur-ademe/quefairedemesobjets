import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from modelsearch.models import IndexEntry

from qfdmd.models import Produit, Synonyme
from search.models import SearchTerm


def _make_index_entry(content_type, object_id):
    return IndexEntry.objects.create(
        content_type=content_type,
        object_id=str(object_id),
    )


@pytest.mark.django_db
class TestPurgeOrphanSearchtermIndex:
    """purge_orphan_searchterm_index removes base IndexEntry rows for
    SearchTerms that have a more specific child, without touching the child's
    own entry or entries for bare SearchTerms. See django-modelsearch #58 for
    why rebuild_modelsearch_index cannot do this on its own."""

    def test_deletes_orphan_base_entry_keeps_child_entry(self):
        produit = Produit.objects.create(nom="Mouchoir en papier")
        synonyme = Synonyme.objects.create(nom="Mouchoir en papier", produit=produit)

        searchterm_ct = ContentType.objects.get_for_model(SearchTerm)
        synonyme_ct = ContentType.objects.get_for_model(Synonyme)

        # Simulate the pre-fix state: the same object indexed twice.
        orphan = _make_index_entry(searchterm_ct, synonyme.searchterm_ptr_id)
        child = _make_index_entry(synonyme_ct, synonyme.searchterm_ptr_id)

        call_command("purge_orphan_searchterm_index")

        assert not IndexEntry.objects.filter(pk=orphan.pk).exists()
        assert IndexEntry.objects.filter(pk=child.pk).exists()

    def test_keeps_bare_searchterm_entry(self):
        bare = SearchTerm.objects.create()
        searchterm_ct = ContentType.objects.get_for_model(SearchTerm)
        entry = _make_index_entry(searchterm_ct, bare.pk)

        call_command("purge_orphan_searchterm_index")

        assert IndexEntry.objects.filter(pk=entry.pk).exists()

    def test_dry_run_deletes_nothing(self):
        produit = Produit.objects.create(nom="Mouchoir en papier")
        synonyme = Synonyme.objects.create(nom="Mouchoir en papier", produit=produit)
        searchterm_ct = ContentType.objects.get_for_model(SearchTerm)
        orphan = _make_index_entry(searchterm_ct, synonyme.searchterm_ptr_id)

        call_command("purge_orphan_searchterm_index", "--dry-run")

        assert IndexEntry.objects.filter(pk=orphan.pk).exists()
