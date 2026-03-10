import pytest
from qfdmo.admin.acteur import SourceResource
from qfdmo.models import Source
from unit_tests.qfdmo.acteur_factory import SourceFactory


@pytest.mark.django_db
def test_source_admin_export_includes_non_empty_fields():
    source1 = SourceFactory(
        libelle="Libelle 1",
        code="code123",
        licence="NO_LICENSE",
        url="https://example.com/1",
        afficher=True,
    )
    source2 = SourceFactory(
        libelle="Libelle 2",
        code="code456",
        licence="CC_BY_NC_SA",
        url="https://example.com/2",
        afficher=False,
    )
    resource = SourceResource()
    dataset = resource.export(Source.objects.filter(id__in=[source1.id, source2.id]))  # type: ignore[arg-type]

    expected_fields = ["libelle", "code", "licence", "url", "afficher"]

    assert dataset.headers is not None
    assert list(dataset.headers) == expected_fields

    assert len(dataset.dict) == 2

    for row in dataset.dict:
        for field in expected_fields:
            assert row[field] not in ("", None)
