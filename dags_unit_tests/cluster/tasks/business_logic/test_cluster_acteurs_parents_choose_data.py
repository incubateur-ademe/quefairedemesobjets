import numpy as np
import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from rich import print

from dags.cluster.config.constants import COL_PARENT_DATA_NEW
from dags.cluster.tasks.business_logic.cluster_acteurs_parents_choose_data import (
    cluster_acteurs_parents_choose_data,
    field_pick_value,
    parent_choose_data,
)
from dags.utils.django import django_setup_full

django_setup_full()

EMPTY_KEEP = True
EMPTY_IGNORE = False


@pytest.fixture
def acteurs_revision():
    # TODO: once we have fixed data validation in field_pick_value
    # replace below values with a mix of good/bad ones and expect
    # the tests to pick the good ones.

    # ❌ = excluded source values

    # Intentionally sorting acteurs with exclusion first and
    # random order vs. prio to test exclusion and picking
    ids = ["a1", "a2", "a3", "a4"]
    noms = ["❌", "prio 2", "prio 1", "prio 3"]
    # With SIRET we are testing picking that data won't be
    # proposed because it's the same
    sirets = ["❌", "11111111111111", None, None]
    # With emails we are testing the fallback to base acteurs
    emails = [None, None, None, None]
    source_ids = [5, 20, 10, 30]
    locations = [Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)]
    return [
        {
            "identifiant_unique": i,
            "nom": n,
            "siret": s,
            "email": e,
            "source_id": sid,
            "location": loc,
            "acteur_type_id": 1,
        }
        for i, n, s, e, sid, loc in zip(
            ids, noms, sirets, emails, source_ids, locations
        )
    ]


@pytest.fixture
def acteurs_base():
    ids = ["a1", "a2", "a3"]
    noms = ["❌", "prio 2", "prio 1"]
    sirets = ["❌", None, None]
    emails = ["❌", "prio2@fallback.base", "prio1@fallback.base"]
    source_ids = [5, 20, 10]
    locations = [Point(0, 0), Point(1, 1), Point(2, 2)]
    return [
        {
            "identifiant_unique": i,
            "nom": n,
            "siret": s,
            "email": e,
            "source_id": sid,
            "location": loc,
            "acteur_type_id": 1,
        }
        for i, n, s, e, sid, loc in zip(
            ids, noms, sirets, emails, source_ids, locations
        )
    ]


@pytest.fixture
def parent():
    return {
        "identifiant_unique": "p1",
        "nom": "my name",
        "siret": "11111111111111",
        "email": "i@me.com",
        # With adresse we are testing fields
        # not included in fields_to_include
        "adresse": "my place",
        "acteur_type_id": 1,
        "source_id": None,
    }


@pytest.fixture
def data_empty_ignore(parent, acteurs_revision, acteurs_base) -> dict:
    data = parent_choose_data(
        parent_data_before=parent,
        acteurs_revision=acteurs_revision,
        acteurs_base=acteurs_base,
        fields_to_include=["nom", "siret", "email"],
        prioritize_source_ids=[10, 20],
        exclude_source_ids=[5],
        keep_empty=EMPTY_IGNORE,
    )
    return data


@pytest.mark.django_db
class TestFieldPickValue:

    @pytest.mark.parametrize(
        "field, values, keep_empty,expected",
        [
            # Currently there is no validation because of .full_clean mess
            # AND métier confirming they want clustering ASAP and are OK
            # with suggestions proposing bad data
            # 💩 = bad data
            # TODO: once validation fixed in field_pick_value, replace
            # below tests to confirm ONLY valid data is ever picked no
            # matter the configuration
            ("email", ["💩", "i@me.com", "💩"], EMPTY_IGNORE, "💩"),
            ("email", [" ", None, "i@me.com", "💩"], EMPTY_IGNORE, "i@me.com"),
            ("email", [" ", None, "i@me.com", "💩"], EMPTY_KEEP, " "),
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
class TestParentChooseData:

    def test_no_values_picked_from_excluded_sources(self, data_empty_ignore):
        assert all(x != "❌" for x in data_empty_ignore.values())

    def test_internal_fields_not_in_data(self, data_empty_ignore):
        internals = ["acteur_type_id", "acteur_type", "source_id", "source"]
        assert all(x not in data_empty_ignore for x in internals)

    def test_nom_from_prio1_as_present(self, data_empty_ignore):
        # It was non-null on prio 1 so we took it
        assert data_empty_ignore["nom"] == "prio 1"

    def test_siret_not_proposed(self, data_empty_ignore):
        # The only good value was on prio 2 BUT it's the
        # same as original so we don't propose it again
        assert "siret" not in data_empty_ignore

    def test_email_fallback_to_base_acteurs(self, data_empty_ignore):
        # All revision acteurs had None emails, so we fallback to base
        # were we picked from 1st prio
        assert data_empty_ignore["email"] == "prio1@fallback.base"

    def test_fields_not_specified_not_included(self, data_empty_ignore):
        # We didn't say we wanted the adresse so we shouldn't have it
        assert "adresse" not in data_empty_ignore


@pytest.mark.django_db
class TestClusterActeursParentsChooseData:

    @pytest.fixture
    def df_clusters_parent_keep(self, parent, acteurs_revision, acteurs_base):
        # TODO: throughout tests we spend WAY too much time defining
        # data, and data is getting progressively more complex throughout
        # pipeline. We should probably use factories or centralise data/fixtures
        from data.models.change import COL_CHANGE_MODEL_NAME
        from data.models.changes import (
            ChangeActeurKeepAsParent,
            ChangeActeurUpdateParentId,
        )

        acteurs = [parent] + acteurs_revision + acteurs_base
        df = pd.DataFrame(acteurs, dtype="object").replace({np.nan: None})
        df[COL_CHANGE_MODEL_NAME] = None
        filter_parent = df["identifiant_unique"] == "p1"
        df.loc[filter_parent, COL_CHANGE_MODEL_NAME] = ChangeActeurKeepAsParent.name()
        df.loc[~filter_parent, COL_CHANGE_MODEL_NAME] = (
            ChangeActeurUpdateParentId.name()
        )
        df["cluster_id"] = "c1"
        return df.drop_duplicates(subset=["identifiant_unique"], keep="first")

    @pytest.fixture
    def df_clusters_parent_create(self, parent, acteurs_revision, acteurs_base):
        # TODO: throughout tests we spend WAY too much time defining
        # data, and data is getting progressively more complex throughout
        # pipeline. We should probably use factories or centralise data/fixtures
        from data.models.change import COL_CHANGE_MODEL_NAME
        from data.models.changes import (
            ChangeActeurCreateAsParent,
            ChangeActeurUpdateParentId,
        )

        acteurs = [parent] + acteurs_revision + acteurs_base
        df = pd.DataFrame(acteurs, dtype="object").replace({np.nan: None})
        df[COL_CHANGE_MODEL_NAME] = None
        filter_parent = df["identifiant_unique"] == "p1"
        df.loc[filter_parent, COL_CHANGE_MODEL_NAME] = ChangeActeurCreateAsParent.name()
        df.loc[~filter_parent, COL_CHANGE_MODEL_NAME] = (
            ChangeActeurUpdateParentId.name()
        )
        df["cluster_id"] = "c1"
        print("df_clusters_parent_create before drops", df.to_dict(orient="records"))
        df = df.drop_duplicates(subset=["identifiant_unique"], keep="first")
        print("df_clusters_parent_create", df.to_dict(orient="records"))
        return df

    @pytest.fixture
    def atype(self):
        from qfdmo.models import ActeurType

        ActeurType(id=1, code="t1").save()

    @pytest.fixture
    def sources(self, acteurs_revision, acteurs_base):
        from qfdmo.models import Source

        for id in set([a["source_id"] for a in acteurs_revision + acteurs_base]):
            Source(id=id, code=f"s{id}").save()

    @pytest.fixture
    def acteurs_revision_to_db(self, acteurs_revision, sources, atype):
        from qfdmo.models import RevisionActeur

        for acteur in acteurs_revision:
            RevisionActeur(**acteur).save()

    @pytest.fixture
    def acteurs_base_to_db(self, acteurs_base, sources, atype):
        from qfdmo.models import Acteur

        for acteur in acteurs_base:
            Acteur(**acteur).save()

    @pytest.mark.parametrize("scenario", ["parent_keep", "parent_create"])
    def test_cluster_acteurs_parents_choose_data(
        self,
        df_clusters_parent_keep,
        df_clusters_parent_create,
        parent,
        acteurs_revision_to_db,
        acteurs_base_to_db,
        data_empty_ignore,
        scenario,
    ):
        from qfdmo.models import DisplayedActeur

        dfs = {
            "parent_keep": df_clusters_parent_keep,
            "parent_create": df_clusters_parent_create,
        }
        df_before = dfs[scenario]

        DisplayedActeur(**parent).save()
        print("BEFORE", df_before.to_dict(orient="records"))
        df_after = cluster_acteurs_parents_choose_data(
            df_clusters=df_before,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[5],
            prioritize_source_ids=[10, 20],
            keep_empty=EMPTY_IGNORE,
        )
        print("AFTER", df_after.to_dict(orient="records"))
        filter_parent = df_after["identifiant_unique"] == "p1"
        parent_data = df_after[filter_parent][COL_PARENT_DATA_NEW].values[0]
        df_children = df_after[~filter_parent]
        if scenario == "parent_create":
            # Since this parent is to create, it doesn't have a siret so we expect
            # to have it
            data_empty_ignore["siret"] = "11111111111111"
        assert parent_data == data_empty_ignore
        assert df_children[COL_PARENT_DATA_NEW].isnull().sum() == len(df_children)

    def test_parent_create(
        self,
        df_clusters_parent_create,
        parent,
        acteurs_revision_to_db,
        acteurs_base_to_db,
        data_empty_ignore,
    ):
        from qfdmo.models import DisplayedActeur

        df_before = df_clusters_parent_create

        DisplayedActeur(**parent).save()
        print("BEFORE", df_before.to_dict(orient="records"))
        df_after = cluster_acteurs_parents_choose_data(
            df_clusters=df_before,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[5],
            prioritize_source_ids=[10, 20],
            keep_empty=EMPTY_IGNORE,
        )
        print("AFTER", df_after.to_dict(orient="records"))
        filter_parent = df_after["identifiant_unique"] == "p1"
        parent_data = df_after[filter_parent][COL_PARENT_DATA_NEW].values[0]
        df_children = df_after[~filter_parent]
        # Since this parent is to create, it doesn't have a siret so we expect
        # to have it
        data_empty_ignore["siret"] = "11111111111111"
        assert parent_data == data_empty_ignore
        assert df_children[COL_PARENT_DATA_NEW].isnull().sum() == len(df_children)
