import pandas as pd
import pytest
from django.contrib.gis.geos import Point

from dags.cluster.tasks.business_logic.cluster_acteurs_parents_choose_data import (
    cluster_acteurs_one_parent_choose_data,
    cluster_acteurs_parents_choose_data,
)
from dags.utils.django import django_setup_full
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    RevisionActeurFactory,
    SourceFactory,
)

django_setup_full()

from qfdmo.models.acteur import RevisionActeur  # noqa: E402

COLS_DATA = [
    "nom",
    "location",
    "siret",
    "email",
    "source_id",
]
EXCL_2, EXCL_3 = 2, 3
PRIO_20, PRIO_10, PRIO_15 = 20, 10, 15


# TODO: Once we have fixed the RevisionActeur full_clean/save mess
# we can re-enable quality tests on the data selection. Not doing inside
# clustering PR as it's beyond scope.
@pytest.mark.django_db
class DISDABLED_TestClusterActeursParentsChooseData:

    @pytest.fixture
    def acteurs(self):
        acteurs = [
            # Intentionnellement un acteur poubelle à la fois
            # premier et avec source_id 1 pour détecter bug 1er
            ["rien de bon", Point(0, 0), "🔴 BAD", "🔴 BAD", 1],
            # SIRET OK: prio à 20
            ["a1 siret OK", Point(0, 0), "11111111111111", "🔴 BAD", EXCL_2],
            ["a2 siret OK", Point(0, 0), "11111111111111", "🔴 BAD", EXCL_3],
            ["a3 siret OK", Point(0, 0), "33333333333333", "🔴 BAD", 30],
            # Un None sur email pour tester consider_empty
            ["a4 siret OK", Point(0, 0), "20202020202020", "🔴 BAD", PRIO_20],
            # EMAIL OK: prio à 10
            ["b1 email OK", Point(0, 0), "🔴 BAD", "2@me.com", EXCL_2],
            ["b2 email OK", Point(0, 0), "🔴 BAD", "3@me.com", EXCL_3],
            ["b3 email OK", Point(0, 0), "🔴 BAD", "30@me.com", 30],
            ["b4 email OK", None, "🔴 BAD", "10@me.com", PRIO_10],
            # LOCATION OK: prio à 15
            ["c1 loc OK", Point(4, 4), "🔴 BAD", "🔴 BAD", EXCL_2],
            ["c2 loc OK", Point(4, 4), "🔴 BAD", "🔴 BAD", EXCL_3],
            ["c3 loc OK", Point(4, 4), "🔴 BAD", "🔴 BAD", 30],
            ["c4 loc OK", Point(15, 15), "🔴 BAD", "🔴 BAD", PRIO_15],
            # Intentionnellement un acteur poubelle à la fois
            # dernier et avec source_id MAX pour détecter bug dernier
            ["rien de bon", Point(0, 0), "🔴 BAD", "🔴 BAD", 666],
        ]
        return [dict(zip(COLS_DATA, a)) for a in acteurs]

    @pytest.fixture
    def not_none(self, acteurs):
        # Résultats pour le mode consider_empty=False
        return cluster_acteurs_one_parent_choose_data(
            acteurs_revision=acteurs,
            acteurs_base=[],
            fields_to_include=["siret", "email", "location"],
            exclude_source_ids=[EXCL_2, EXCL_3],
            prioritize_source_ids=[PRIO_20, PRIO_10, PRIO_15],
            consider_empty=False,
        )

    def test_not_none_only_selected_fields(self, not_none):
        # Avec nom manquant on démontre que seuls les champs
        # désirés sont retournés
        assert sorted(not_none.keys()) == sorted(["siret", "email", "location"])

    def test_not_none_siret_from_source_20(self, not_none):
        # La 1ère source de prio est également celle à avoir un bon siret
        assert not_none["siret"] == "20202020202020"

    def test_not_none_email_from_source_10(self, not_none):
        # Bien que source 20 ait un email, il est mauvais
        # donc c'est bien 10 qui est choisi
        assert not_none["email"] == "10@me.com"

    def test_not_none_location_from_source_15(self, not_none):
        # Toutes les sources ont bien une location, mais on considère
        # Point(0,0) comme mauvais donc c'est bien 15 qui est choisi
        assert str(not_none["location"]) == str(Point(15, 15))

    @pytest.fixture
    def consider_empty(self, acteurs):
        # Résultats pour le mode consider_empty=True
        return cluster_acteurs_one_parent_choose_data(
            acteurs_revision=acteurs,
            acteurs_base=[],
            fields_to_include=["siret", "email", "location"],
            exclude_source_ids=[EXCL_2, EXCL_3],
            prioritize_source_ids=[PRIO_20, PRIO_10, PRIO_15],
            consider_empty=True,
        )

    def test_keep_none_colmuns(self, consider_empty):
        # Pas de changement sur les colonnes
        assert sorted(consider_empty.keys()) == sorted(["siret", "email", "location"])

    def test_keep_none_siret_unchanged(self, consider_empty):
        # Pas de changement sur le siret
        assert consider_empty["siret"] == "20202020202020"

    def test_keep_none_email_unchanged(self, consider_empty):
        # Pas de changement sur l' email
        assert consider_empty["email"] == "10@me.com"

    def test_keep_none_location_is_none(self, consider_empty):
        # Maintenent qu'on consèrve les None, on a b4 email OK
        # de la source 10 qui a une location None et qui
        # donc prend priorité
        assert consider_empty["location"] is None

    def test_fields_to_include_clean(self, acteurs):
        # Par sécurité, la fonction comprends une logique
        # d'exclusion des champs internes & calculés qu'on
        # ne doit pas récupérer
        result = cluster_acteurs_one_parent_choose_data(
            acteurs_revision=acteurs,
            acteurs_base=[],
            fields_to_include=["siret", "source_id", "nombre_enfants"],
            exclude_source_ids=[EXCL_2, EXCL_3],
            prioritize_source_ids=[PRIO_20, PRIO_10, PRIO_15],
            consider_empty=True,
        )
        assert result.keys() == {"siret"}

    def test_no_priority_eq_in_order_of_validity(self, acteurs):
        # Quand on ne spécifie aucune source, on prend la donnée
        # par l'ordre d'apparition à condition qu'elle soit valide
        result = cluster_acteurs_one_parent_choose_data(
            acteurs_revision=acteurs,
            acteurs_base=[],
            fields_to_include=["siret", "email", "location"],
            exclude_source_ids=[],
            prioritize_source_ids=[],
            consider_empty=True,
        )
        assert result["siret"] == "11111111111111"
        assert result["email"] == "2@me.com"
        assert str(result["location"]) == str(Point(4, 4))


@pytest.mark.django_db
class TestClusterActeursParentsChooseData:

    @pytest.fixture
    def acteurs(self):
        # What we're testing:
        # siret: there is a good value in a Revision -> take it
        # location: there is a good value in Base -> take it
        # email: there is no good value -> so we fallback to bad data
        # adresse: no value anywhere -> not present in result
        # We are also demonstrating for email that we can 🔴 BAD
        # because we have yet to fix cluster_acteurs_one_parent_choose_data

        s1 = SourceFactory(code="s1")  # 🟠 not prio = fallback
        s2 = SourceFactory(code="s2")  # 1️⃣ prio
        s3 = SourceFactory(code="s3")  # 1️⃣ prio
        s_excluded = SourceFactory(code="EXCLUDED")  # ❌ excluded

        # ----------------------------
        # Cluster 1
        # ----------------------------
        # Intentionally creating 1st acteur on excluded source and putting
        # good values on it to show that exclusion technically works at source
        # level and not based on data quality (even though that's the intention)
        r1 = RevisionActeurFactory(
            source=s_excluded,
            email="r1@me.com",
            siret="11111111111111",
            location=Point(5, 5),
            adresse="Rue de l'exclu",
        )
        p = RevisionActeur(
            source=s_excluded,
            email="r1@me.com",
            siret="11111111111111",
            location=Point(5, 5),
            adresse="Rue du parent",
        )
        r2 = RevisionActeurFactory(source=s1, email="🔴 BAD")
        r3 = RevisionActeurFactory(source=s2, siret="11111111111111")
        # TODO: add to clean_location: convert Point(0,0) to None
        ActeurFactory(identitiant_unique=r2.pk, source=s3, location=Point(0, 0))
        ActeurFactory(identitiant_unique=r3.pk, source=s3, adresse=None)

        df_clusters = pd.DataFrame(
            {
                "cluster_id": ["c1", "c1", "c1", "c1"],
                "identifiant_unique": [r1.pk, r2.pk, r3.pk, p.pk],
            }
        )

        results = cluster_acteurs_parents_choose_data(
            df_clusters=df_clusters,
            fields_to_include=["siret", "email", "location", "adresse"],
            exclude_source_ids=[s_excluded.pk],
            prioritize_source_ids=[s2.pk, s3.pk],
            consider_empty=False,
        )
        print(f"{results=}")
