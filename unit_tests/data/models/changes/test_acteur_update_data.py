"""
Test file for the ChangeActeurUpdateData model.

"""

import pytest
from django.contrib.gis.geos import Point
from pydantic import ValidationError

from dags.sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from data.models.changes.acteur_update_data import ChangeActeurUpdateData
from qfdmo.models.acteur import Acteur, ActeurType, RevisionActeur


@pytest.mark.django_db
class TestChangeActeurUpdateData:
    def test_name(self):
        assert ChangeActeurUpdateData.name() == "acteur_update_data"

    def test_raise_if_no_data_provided(self):
        change = ChangeActeurUpdateData(id="dummy", data={})
        with pytest.raises(ValueError, match="No data provided"):
            change.apply()

    @pytest.mark.parametrize("data", [None, True])
    def test_raise_if_data_wrong_type(self, data):
        with pytest.raises(ValidationError):
            ChangeActeurUpdateData(id="dummy", data=data)

    def test_raise_if_acteur_does_not_exist(self):
        change = ChangeActeurUpdateData(id="dummy", data={"nom": "test"})
        with pytest.raises(Acteur.DoesNotExist):
            change.apply()

    def test_working_case(self):
        # We start by creating acteur only in base
        at1 = ActeurType.objects.create(code="at1")
        at2 = ActeurType.objects.create(code="at2")
        base = Acteur.objects.create(nom="test", acteur_type=at1, location=Point(1, 2))

        # We check that acteur isn't in revision yet
        assert RevisionActeur.objects.filter(pk=base.pk).count() == 0

        # Then we modify its data, notably some Python and Django types
        data = {"nom": "test2", "acteur_type": at2.pk, "location": Point(2, 3)}
        ChangeActeurUpdateData(id=base.pk, data=data).apply()

        # We check that acteur was created in revision with the right data
        rev = RevisionActeur.objects.get(pk=base.pk)
        assert rev.nom == "test2"
        assert rev.acteur_type == at2
        assert rev.location.x == 2
        assert rev.location.y == 3

        # We check that acteur in base wasn't modified
        base = Acteur.objects.get(pk=base.pk)
        assert base.nom == "test"
        assert base.acteur_type == at1
        assert base.location.x == 1
        assert base.location.y == 2

        # If we perform the some changes again, revision is again
        # updated AND there is no conflit / creation of a new revision
        data = {"nom": "test3"}
        ChangeActeurUpdateData(id=base.pk, data=data).apply()
        rev = RevisionActeur.objects.get(pk=base.pk)
        assert rev.nom == "test3"
        assert rev.acteur_type == at2
        assert RevisionActeur.objects.filter(pk=base.pk).count() == 1

    def test_set_to_empty(self):
        # This is a special case for the Crawl URLs DAG
        # which prompted to create this change model, so we
        # need to ensure that specific case works
        at1 = ActeurType.objects.create(code="at1")
        base = Acteur.objects.create(
            nom="test", acteur_type=at1, location=Point(1, 2), url="https://example.com"
        )
        data = {"url": EMPTY_ACTEUR_FIELD}
        ChangeActeurUpdateData(id=base.pk, data=data).apply()
        rev = RevisionActeur.objects.get(pk=base.pk)
        assert rev.url == EMPTY_ACTEUR_FIELD
