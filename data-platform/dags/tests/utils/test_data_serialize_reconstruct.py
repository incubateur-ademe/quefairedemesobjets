from datetime import datetime

import pytest
from django.contrib.gis.geos import Point

from data.models.changes.utils import data_reconstruct
from qfdmo.models.acteur import RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    ActionFactory,
    SourceFactory,
)
from utils.data_serialize_reconstruct import data_serialize

DATETIME = datetime(2023, 10, 1, 14, 30, 4)
POINT = Point(1, 2)


@pytest.mark.django_db
class TestDataSerializeReconstruct:

    @pytest.fixture
    def data_init(self) -> dict:
        s = SourceFactory(code="my_source")
        action = ActionFactory(code="my_acteur_type")
        at = ActeurTypeFactory(code="my_action")
        data = {
            "nom": "un acteur",
            "identifiant_unique": "test",
            "source": s,
            "acteur_type": at,
            "action_principale": action,
            "location": POINT,
            "cree_le": DATETIME,
        }
        return data

    @pytest.fixture
    def data_serialized(self, data_init) -> dict:
        data = data_serialize(RevisionActeur, data_init)
        return data

    @pytest.fixture
    def data_reconstructed(self, data_serialized) -> dict:
        data = data_reconstruct(RevisionActeur, data_serialized)
        return data

    def test_data_reconstructed(self, data_reconstructed):
        data = data_reconstructed
        assert data["location"].x == POINT.x
        assert data["location"].y == POINT.y
        assert isinstance(data["cree_le"], str)

    def test_data_reconstructed_compatible_with_model(self, data_reconstructed):
        rev = RevisionActeur(**data_reconstructed)
        rev.save()
        # FIXME: setting cree_le doesn't work the 1st time due
        # to auto_now_add on our model:
        # "Automatically set the field to now when the object is first created"
        assert rev.cree_le.isoformat() != DATETIME.isoformat()

        # Now cree_le is properly updated
        rev.cree_le = data_reconstructed["cree_le"]
        rev.save()
        assert rev.cree_le.isoformat() == DATETIME.isoformat()

    def test_none_cases(self, data_init):
        # Special case for location which is forbidden
        # non non-digital acteurs BUT we have no way of
        # knowing what type of acteur we're dealing with
        # as data could be partial (e.g. in the clustering
        # pipeline where we only suggest diffs for parents)
        data = data_init.copy()
        data["location"] = None
        # Special case on foreign key fields
        data["parent"] = None
        data = data_serialize(RevisionActeur, data)
        data = data_reconstruct(RevisionActeur, data)

        # Consequence for location=None is that we don't
        # reflect it in the reconstructed data
        assert "location" not in data

        # For parent=None we keep value as None
        assert data["parent"] is None

        # We ensure that the location bypass isn't possible
        # if we try to reconstruct directly
        data = {"location": None}
        data = data_reconstruct(RevisionActeur, data)
        assert data == {}

    def test_working_with_id_fields(self, data_init):
        # When working with DBT, we have foreign keys being
        # expressed as {field}_id fields (and not {field} like
        # in Django models), and we test that data_reconstruct
        # handles this transparently and forces {field} representation
        data = data_init.copy()
        # We switch from the Django reprentation (source) to the
        # DBT representation (source_id)
        data["source_id"] = data["source"].id
        del data["source"]
        ser = data_serialize(RevisionActeur, data)
        rec = data_reconstruct(RevisionActeur, ser)
        # The reconstruction should be in {field} format
        assert rec["source"].id == data_init["source"].id
