import pandas as pd
import pytest
from django.contrib.gis.geos import Point

from dags.cluster.tasks.business_logic.cluster_acteurs_parents_choose_data import (
    cluster_acteurs_parents_choose_data,
    field_pick_value,
    fields_to_include_clean,
    value_is_empty,
)
from data.models.changes.acteur_create_as_parent import ChangeActeurCreateAsParent
from data.models.changes.acteur_keep_as_parent import ChangeActeurKeepAsParent
from data.models.changes.acteur_update_parent_id import ChangeActeurUpdateParentId
from data.models.changes.acteur_verify_in_revision import ChangeActeurVerifyRevision
from qfdmo.models.acteur import RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    RevisionActeurFactory,
    SourceFactory,
)
from utils.django import django_setup_full

django_setup_full()


@pytest.fixture
def acteur_type():
    return ActeurTypeFactory(code="t1")


@pytest.fixture
def sources():
    return [SourceFactory() for _ in range(4)]


@pytest.fixture
def acteurs(acteur_type, sources):
    ids = ["a1", "a2", "a3"]
    noms = ["❌", "prio 2", "prio 1"]
    sirets = ["❌", "", ""]
    emails = ["email.acteur@source.1", "email.acteur@source.2", "email.acteur@source.3"]
    locations = [Point(0, 0), Point(1, 1), Point(2, 2)]
    return [
        ActeurFactory(
            identifiant_unique=i,
            nom=n,
            siret=s,
            email=e,
            source=source,
            location=loc,
            acteur_type=acteur_type,
        )
        for i, n, s, e, source, loc in zip(
            ids, noms, sirets, emails, sources[:3], locations
        )
    ]


@pytest.fixture
def parent(acteur_type):
    return RevisionActeur(
        identifiant_unique="p1",
        nom="my name",
        siret="11111111111111",
        email="",  # empty value
        acteur_type=acteur_type,
        adresse="my place",
        source=None,
    ).save_as_parent()


@pytest.fixture
def revision_acteurs(acteur_type, sources, parent, acteurs):
    ids = ["a1", "a2", "a3", "a4"]
    noms = ["❌", "prio 2", "prio 1", "prio 3"]
    # With SIRET we are testing picking that data won't be
    # proposed because it's the same
    sirets = ["❌", "11111111111111", "", ""]
    # With emails we are testing the fallback to base acteurs
    emails = ["", "", "", ""]
    locations = [Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)]
    parents = [parent, parent, None, None]
    return [
        RevisionActeurFactory(
            identifiant_unique=i,
            nom=n,
            siret=s,
            email=e,
            source=source,
            location=loc,
            parent=parent,
            acteur_type=acteur_type,
        )
        for i, n, s, e, source, loc, parent in zip(
            ids, noms, sirets, emails, sources[:4], locations, parents
        )
    ]


class TestFieldsToIncludeClean:
    @pytest.mark.parametrize(
        "fields_to_include, expected",
        [
            (["nom", "siret", "email"], ["nom", "siret", "email"]),
            (
                [
                    "nom",
                    "siret",
                    "proposition_services",
                    "source",
                    "source_id",
                    "statut",
                    "cree_le",
                    "modifie_le",
                    "identifiant_unique",
                    "identifiant_externe",
                    "email",
                ],
                ["nom", "siret", "email"],
            ),
        ],
    )
    def test_fields_to_include_clean(self, fields_to_include, expected):
        assert fields_to_include_clean(fields_to_include) == expected


class TestValueIsEmpty:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (None, True),
            ("", True),
            (" ", True),
            ("i@me.com", False),
        ],
    )
    def test_value_is_empty(self, value, expected):
        assert value_is_empty(value) == expected


@pytest.mark.django_db
class TestFieldPickValue:

    @pytest.mark.parametrize(
        "field, values, keep_empty,expected",
        [
            ("email", ["💩", "i@me.com", "💩"], False, "💩"),
            ("email", [" ", None, "i@me.com", "💩"], False, "i@me.com"),
            ("email", [" ", None, "i@me.com", "💩"], True, " "),
        ],
    )
    def test_acteurs_get_one_field(self, field, values, keep_empty, expected):
        assert (
            field_pick_value(
                field,
                values,
                keep_empty,
            )
            == expected
        )


@pytest.mark.django_db
class TestClusterActeursParentsChooseData:

    @pytest.fixture
    def df_clusters_parent_keep(self, acteurs, parent, revision_acteurs):

        return pd.DataFrame(
            {
                "cluster_id": ["c1"] * 5,
                "change_order": [1, 2, 2, 2, 2],
                "change_reason": ["", "", "", "", ""],
                "change_model_name": [
                    ChangeActeurKeepAsParent.name(),
                    ChangeActeurVerifyRevision.name(),
                    ChangeActeurVerifyRevision.name(),
                    ChangeActeurUpdateParentId.name(),
                    ChangeActeurUpdateParentId.name(),
                ],
                "identifiant_unique": ["p1", "a1", "a2", "a3", "a4"],
                "parent_id": [None, "p1", "p1", None, None],
            }
        )

    @pytest.fixture
    def df_clusters_parent_create(self, parent, revision_acteurs, acteurs):
        return pd.DataFrame(
            {
                "cluster_id": ["c2"] * 3,
                "change_order": [1, 2, 2],
                "change_reason": ["", "", ""],
                "change_model_name": [
                    ChangeActeurCreateAsParent.name(),
                    ChangeActeurUpdateParentId.name(),
                    ChangeActeurUpdateParentId.name(),
                ],
                "identifiant_unique": ["p1", "a3", "a4"],
                "parent_id": [None, None, None],
            }
        )

    def test_cluster_acteurs_parents_choose_data_parent_keep(
        self,
        df_clusters_parent_keep,
        sources,
    ):
        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_keep,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[sources[0].id, sources[1].id],
            keep_empty=False,
        )

        # Retrieve parent data
        assert df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[
            0
        ] == {"email": "email.acteur@source.1"}
        # tester que tous les autres sont None
        assert (
            df.loc[df["identifiant_unique"] != "p1", "parent_data_new"].isnull().all()
        )

    def test_cluster_acteurs_parents_choose_data_parent_create(
        self,
        df_clusters_parent_create,
        sources,
    ):
        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_create,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[sources[2].id],
            keep_empty=False,
        )

        # Retrieve parent data
        assert df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[
            0
        ] == {"nom": "prio 1", "email": "email.acteur@source.3"}
        # tester que tous les autres sont None
        assert (
            df.loc[df["identifiant_unique"] != "p1", "parent_data_new"].isnull().all()
        )
