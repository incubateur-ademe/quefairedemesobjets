import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from utils.django import django_setup_full

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
from qfdmo.models.acteur import VueActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    SourceFactory,
    VueActeurFactory,
)

django_setup_full()


@pytest.fixture
def acteur_type():
    return ActeurTypeFactory(code="t1")


@pytest.fixture
def sources():
    return [SourceFactory() for _ in range(4)]


@pytest.fixture
def parent(acteur_type, sources):
    """Parent acteur pour les tests"""
    return VueActeurFactory(
        identifiant_unique="p1",
        nom="my name",
        siret="11111111111111",
        email="",  # empty value
        acteur_type=acteur_type,
        adresse="my place",
        sources=sources,
    )


@pytest.fixture
def vue_acteurs(acteur_type, sources, parent):
    """Tous les VueActeur nécessaires pour les tests"""
    return [
        # a1: with email, parent=p1, to test the email retrieval
        VueActeurFactory(
            identifiant_unique="a1",
            nom="❌",
            siret="❌",
            email="email.acteur@source.1",
            sources=[sources[0]],
            location=Point(0, 0),
            parent=parent,
            acteur_type=acteur_type,
        ),
        # a2: with email, parent=p1, same SIRET as parent
        VueActeurFactory(
            identifiant_unique="a2",
            nom="prio 2",
            siret="11111111111111",  # same SIRET as parent
            email="email.acteur@source.2",
            sources=[sources[1]],
            location=Point(1, 1),
            parent=parent,
            acteur_type=acteur_type,
        ),
        # a3: with email, no parent, to test parent creation
        VueActeurFactory(
            identifiant_unique="a3",
            nom="prio 1",
            siret="",
            email="email.acteur@source.3",
            sources=[sources[2]],
            location=Point(2, 2),
            parent=None,
            acteur_type=acteur_type,
        ),
        # a4: without email, no parent, to test empty emails
        VueActeurFactory(
            identifiant_unique="a4",
            nom="prio 3",
            siret="",
            email="",  # empty email
            sources=[sources[3]],
            location=Point(3, 3),
            parent=None,
            acteur_type=acteur_type,
        ),
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
        "values, keep_empty, expected",
        [
            (["💩", "i@me.com", "💩"], False, "💩"),
            ([" ", None, "i@me.com", "💩"], False, "i@me.com"),
            ([" ", None, "i@me.com", "💩"], True, " "),
        ],
    )
    def test_field_pick_value(self, values, keep_empty, expected):
        assert (
            field_pick_value(
                values,
                keep_empty,
            )
            == expected
        )


@pytest.mark.django_db
class TestClusterActeursParentsChooseData:
    @pytest.fixture
    def df_clusters_parent_keep(self, vue_acteurs, parent):
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
    def df_clusters_parent_create(self, vue_acteurs, parent):
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
        # test that all others are None
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
        ] == {
            "nom": "prio 1",
            "email": "email.acteur@source.3",
        }
        assert (
            df.loc[df["identifiant_unique"] != "p1", "parent_data_new"].isnull().all()
        ), "tester que tous les autres sont None"

    def test_cluster_acteurs_parents_choose_data_parent_keep_keep_empty(
        self,
        df_clusters_parent_keep,
        sources,
    ):
        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_keep,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[sources[0].id, sources[1].id],
            keep_empty=True,
        )

        # Retrieve parent data
        assert (
            df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[0] == {}
        ), (
            "keep_empty is True, first email is empty, as it is the same than parent"
            " email value, the update in empty"
        )
        # test that all others are None
        assert (
            df.loc[df["identifiant_unique"] != "p1", "parent_data_new"].isnull().all()
        )

    def test_cluster_acteurs_parents_choose_data_parent_create_keep_empty(
        self,
        df_clusters_parent_create,
        sources,
    ):
        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_create,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[sources[2].id],
            keep_empty=True,
        )

        # Retrieve parent data
        assert df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[
            0
        ] == {
            "nom": "prio 1",
            "email": "email.acteur@source.3",
        }, (
            "keep_empty is forced to False and the empty email is ignored until"
            " found `email.acteur@source.3`"
        )
        assert (
            df.loc[df["identifiant_unique"] != "p1", "parent_data_new"].isnull().all()
        ), "tester que tous les autres sont None"

    def test_cluster_acteurs_parents_choose_data_parent_create_source_priority(
        self,
        df_clusters_parent_create,
    ):
        vue_a3 = VueActeur.objects.get(identifiant_unique="a3")
        source = vue_a3.source
        assert source is not None, "vue_a3 should have a source"
        vue_a3.source = None
        vue_a3.save()

        # Récupérer a4 qui a une source
        vue_a4 = VueActeur.objects.get(identifiant_unique="a4")
        assert vue_a4.source is not None, "vue_a4 should have a source"
        nom_a4 = vue_a4.nom

        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_create,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[source.id],
            keep_empty=False,
        )

        # Retrieve parent data
        # With VueActeur, if a3 doesn't have a source, it will be sorted after a4
        # which has a source, so a4 will be chosen
        assert (
            df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[0]["nom"]
            == nom_a4
        ), (
            "vue acteur a4 should be chosen because a3 doesn't have "
            "a source defined and a4 has a source"
        )

    def test_cluster_acteurs_parents_choose_data_parent_create_resolve_source_priority(
        self,
        df_clusters_parent_create,
    ):
        vue_a3 = VueActeur.objects.get(identifiant_unique="a3")
        source = vue_a3.source
        assert source is not None, "vue_a3 should have a source"
        vue_a3.nom = ""
        vue_a3.save()

        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_create,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[source.id],
            keep_empty=False,
        )

        # Retrieve parent data
        assert df.loc[df["identifiant_unique"] == "p1", "parent_data_new"].values[0][
            "nom"
        ] not in [
            ""
        ], "vue acteur a3 should not be chosen even if it doesn't have `nom` defined"

    def test_cluster_acteurs_parents_choose_data_parent_create_resolve_empty_nom(
        self,
        df_clusters_parent_create,
    ):
        # Update all VueActeur with empty nom except a3 which will be updated after
        VueActeur.objects.exclude(identifiant_unique="a3").update(nom="")
        vue_a3 = VueActeur.objects.get(identifiant_unique="a3")
        source = vue_a3.source
        assert source is not None, "vue_a3 should have a source"
        vue_a3.nom = ""
        vue_a3.save()

        df = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters_parent_create,
            fields_to_include=["nom", "siret", "email"],
            exclude_source_ids=[],
            prioritize_source_ids=[source.id],
            keep_empty=False,
        )

        # Retrieve parent data
        # If all noms are empty, the result should be None or empty
        parent_data = df.loc[
            df["identifiant_unique"] == "p1", "parent_data_new"
        ].values[0]
        assert (
            "nom" not in parent_data or parent_data.get("nom") == ""
        ), "Si tous les noms sont vides, aucun nom ne devrait être choisi"
