from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from cluster.config.constants import COL_PARENT_DATA_NEW, COL_PARENT_ID_BEFORE
from cluster.helpers.shorthands.change_model_name import (
    CHANGE_CREATE,
    CHANGE_DELETE,
    CHANGE_KEEP,
    CHANGE_NOTHING,
    CHANGE_POINT,
)
from cluster.helpers.shorthands.change_order import O1, O2, O3
from cluster.tasks.business_logic.cluster_acteurs_suggestions.prepare import (
    cluster_acteurs_suggestions_prepare,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.to_db import (
    cluster_acteurs_suggestions_to_db,
)

from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
)
from data.models.suggestion import Suggestion, SuggestionCohorte
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    RevisionActeurFactory,
    SourceFactory,
)

# Shorthands for tests
C1 = "cluster_1"
C2 = "cluster_2"
C3 = "cluster_3"
DATA_ACTEURS = [
    # c1 = new cluster with parent to create
    # & orphan to link
    {
        "cluster_id": C1,
        "identifiant_unique": "c1pcreate",
        "nom": "c1pcreate",
        "parent_id": None,
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O1,
        COL_CHANGE_MODEL_NAME: CHANGE_CREATE,
        COL_CHANGE_REASON: "r_create",
        COL_PARENT_DATA_NEW: {"nom": "new name c1pcreate"},
    },
    {
        "cluster_id": C1,
        "identifiant_unique": "c1orphan1",
        "nom": "c1orphan1",
        "parent_id": "c1pcreate",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_POINT,
        COL_CHANGE_REASON: "r_point",
        COL_PARENT_DATA_NEW: None,
    },
    # c2 = unchanged except for updating parent's data
    {
        "cluster_id": C2,
        "identifiant_unique": "c2pkeep",
        "nom": "c2pkeep",
        "parent_id": None,
        "nombre_enfants": 1,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O1,
        COL_CHANGE_MODEL_NAME: CHANGE_KEEP,
        COL_CHANGE_REASON: "r_point",
        COL_PARENT_DATA_NEW: {"nom": "new name c2pkeep"},
    },
    {
        "cluster_id": C2,
        "identifiant_unique": "c2child1",
        "nom": "c2child1",
        "parent_id": "c2pkeep",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: "c2pkeep",
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_NOTHING,
        COL_CHANGE_REASON: "r_point",
        COL_PARENT_DATA_NEW: {"parent_id": "c2pkeep"},
    },
    # c3 = 2 parents, one with most children kept, other deleted
    # all children/orphans updated to point to kept parent
    {
        "cluster_id": C3,
        "identifiant_unique": "c3pkeep",
        "nom": "c3pkeep",
        "parent_id": None,
        "nombre_enfants": 2,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O1,
        COL_CHANGE_MODEL_NAME: CHANGE_KEEP,
        COL_CHANGE_REASON: "r_create",
        COL_PARENT_DATA_NEW: {"nom": "new name c3pkeep"},
    },
    {
        "cluster_id": C3,
        "identifiant_unique": "c3child1_pkeep",
        "nom": "c3child1_pkeep",
        "parent_id": "c3pkeep",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: "c3pkeep",
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_NOTHING,
        COL_CHANGE_REASON: "already good",
        COL_PARENT_DATA_NEW: None,
    },
    {
        "cluster_id": C3,
        "identifiant_unique": "c3child2_pkeep",
        "nom": "c3child2_pkeep",
        "parent_id": "c3pkeep",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: "c3pkeep",
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_NOTHING,
        COL_CHANGE_REASON: "already good",
        COL_PARENT_DATA_NEW: None,
    },
    {
        "cluster_id": C3,
        "identifiant_unique": "c3child1_pdelete",
        "nom": "c3child1_pdelete",
        "parent_id": "c3pkeep",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: "c3pdelete",
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_POINT,
        COL_CHANGE_REASON: "point to parent to keep",
        COL_PARENT_DATA_NEW: {"parent_id": "c3pkeep"},
    },
    {
        "cluster_id": C3,
        "identifiant_unique": "c3orphan",
        "nom": "c3orphan",
        # TODO: it is confusing to use the same column
        # interchangeably to refer to a child's existing parent
        # AND an orphan's new parent. Refactor dedup_parent_choose
        # to reflect the change of parent in COL_CHANGE_MODEL_PARAMS
        # just like any other data the change model is relying on
        # AND simplify cluster_acteurs_suggestions_prepare which
        # then should have 0 conditional logic (just packaging suggestions)
        "parent_id": "c3pkeep",
        "nombre_enfants": 0,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O2,
        COL_CHANGE_MODEL_NAME: CHANGE_POINT,
        COL_CHANGE_REASON: "point to parent to keep",
        COL_PARENT_DATA_NEW: None,
    },
    {
        "cluster_id": C3,
        "identifiant_unique": "c3pdelete",
        "nom": "c3pdelete",
        "parent_id": None,
        "nombre_enfants": 1,
        COL_PARENT_ID_BEFORE: None,
        COL_CHANGE_ORDER: O3,
        COL_CHANGE_MODEL_NAME: CHANGE_DELETE,
        COL_CHANGE_REASON: "parent to delete",
        COL_PARENT_DATA_NEW: None,
    },
]
# Adding clustering details needed for suggestion contexte
for i, acteur in enumerate(DATA_ACTEURS):
    # We intentionally do not set data on parents to
    # create because in the pipelien that's how they
    # are represented (with 0 actual data, only proposition
    # data in the suggestion's change model params)
    if acteur[COL_CHANGE_MODEL_NAME] != CHANGE_CREATE:
        acteur["ville"] = "laval"
        acteur["adresse"] = f"mon adresse {i}"
CLUSTER_FIELDS_EXACT = ["ville"]
CLUSTER_FIELDS_FUZZY = ["adresse"]


@pytest.mark.django_db()
class TestClusterActeursSuggestionsToDb:
    @pytest.fixture
    def df(self):
        return pd.DataFrame(DATA_ACTEURS).replace({np.nan: None})

    @pytest.fixture
    def db_acteurs_mock(self, df):
        s1 = SourceFactory(code="s1")
        at1 = ActeurTypeFactory(code="at1")
        df = df.copy()
        df["existing_parent"] = df[COL_CHANGE_MODEL_NAME].map(
            lambda x: 1 if x in [CHANGE_KEEP, CHANGE_DELETE] else 0
        )
        df = df.sort_values(by="existing_parent", ascending=False)
        parents = {}
        for _, row in df.iterrows():
            model_name = row[COL_CHANGE_MODEL_NAME]
            if model_name in [CHANGE_KEEP, CHANGE_DELETE]:
                rev = RevisionActeurFactory(
                    source=None,
                    acteur_type=at1,
                    identifiant_unique=row["identifiant_unique"],
                    nom=row["identifiant_unique"],
                )
                DisplayedActeurFactory(
                    acteur_type=at1,
                    identifiant_unique=row["identifiant_unique"],
                    nom=row["identifiant_unique"],
                    sources=[s1],
                )
                parents[row["identifiant_unique"]] = rev
            # No acteur to mock if it's to be created
            elif model_name == CHANGE_CREATE:
                pass
            elif model_name == CHANGE_POINT:
                # TODO: we have 2 cases of pointining
                # -orphans pointing to a parent for first time
                # -children changing parents
                # We should create distinct change models for each case
                # to reduce confusion & conditional code
                parent = (
                    parents[row[COL_PARENT_ID_BEFORE]]
                    if (
                        row[COL_PARENT_ID_BEFORE]
                        and "create" not in row[COL_PARENT_ID_BEFORE]
                    )
                    else None
                )
                RevisionActeurFactory(
                    source=s1,
                    acteur_type=at1,
                    identifiant_unique=row["identifiant_unique"],
                    nom=row["identifiant_unique"],
                    parent=parent,
                )
            elif model_name == CHANGE_NOTHING:
                parent = parents[row[COL_PARENT_ID_BEFORE]]
                RevisionActeurFactory(
                    source=s1,
                    acteur_type=at1,
                    identifiant_unique=row["identifiant_unique"],
                    nom=row["identifiant_unique"],
                    parent=parent,
                )
            else:
                raise ValueError(f"Unhandled {model_name=}")

    @pytest.fixture
    def now(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @pytest.fixture
    def id_action(self, now):
        return f"test action {now}"

    @pytest.fixture
    def id_execution(self, now):
        return f"test execution {now}"

    @pytest.fixture
    def suggestions_list(self, df, db_acteurs_mock) -> list[dict]:
        working, failing = cluster_acteurs_suggestions_prepare(df)
        return working

    @pytest.fixture(autouse=True)
    def suggestions_to_db(self, df, id_action, id_execution, suggestions_list):
        cluster_acteurs_suggestions_to_db(
            df_clusters=df,
            suggestions=suggestions_list,
            identifiant_action=id_action,
            identifiant_execution=id_execution,
            cluster_fields_exact=CLUSTER_FIELDS_EXACT,
            cluster_fields_fuzzy=CLUSTER_FIELDS_FUZZY,
        )

    @pytest.fixture
    def cohorts(self, id_action, id_execution):
        return SuggestionCohorte.objects.filter(
            identifiant_action=id_action, identifiant_execution=id_execution
        )

    @pytest.fixture
    def suggestions_from_db(self, cohorts):
        return Suggestion.objects.filter(suggestion_cohorte=cohorts.first())

    def test_one_cohort_created_per_run(self, cohorts):
        # 1 cohorte par run
        assert cohorts.count() == 1

    def test_one_suggestion_per_cluster(self, df, suggestions_from_db):
        # Autant de suggestions que de clusters
        assert suggestions_from_db.count() == df["cluster_id"].nunique()

    def test_each_suggestion_has_one_change_per_acteur(self, df, suggestions_from_db):
        # Going through each suggestion to test its content
        cluster_ids_found = set()
        for s in suggestions_from_db:
            cluster_id = s.contexte["cluster_id"]
            changes = s.suggestion["changes"]
            cluster_ids_found.add(cluster_id)

            # We should have 1 change matching each of the cluster's acteurs ID
            cluster = df[df["cluster_id"] == cluster_id]
            assert len(cluster) == len(changes)
            assert sorted(cluster["identifiant_unique"].tolist()) == sorted(
                [x["model_params"]["id"] for x in changes]
            )

        # There should be 1 suggestion per cluster
        cluster_ids_missing = set(df["cluster_id"].unique()) - cluster_ids_found
        assert not cluster_ids_missing

    def test_apply_suggestions(self, suggestions_from_db):
        from qfdmo.models.acteur import RevisionActeur

        for suggestion in suggestions_from_db:
            suggestion.apply()

        # Once suggestions have been applied, all acteurs
        # should be in the desired state

        # Cluster 1
        c1pcreate = RevisionActeur.objects.get(pk="c1pcreate")
        assert c1pcreate.nom == "new name c1pcreate"
        c1orphan1 = RevisionActeur.objects.get(pk="c1orphan1")
        assert c1orphan1.parent.identifiant_unique == c1pcreate.identifiant_unique

        # Cluster 2
        c2pkeep = RevisionActeur.objects.get(pk="c2pkeep")
        assert c2pkeep.nom == "new name c2pkeep"
        c2child1 = RevisionActeur.objects.get(pk="c2child1")
        assert c2child1.parent.identifiant_unique == c2pkeep.identifiant_unique

        # Cluster 3
        c3pkeep = RevisionActeur.objects.get(pk="c3pkeep")
        assert c3pkeep.nom == "new name c3pkeep"
        c3child1_pkeep = RevisionActeur.objects.get(pk="c3child1_pkeep")
        assert c3child1_pkeep.parent.identifiant_unique == c3pkeep.identifiant_unique
        c3child2_pkeep = RevisionActeur.objects.get(pk="c3child2_pkeep")
        assert c3child2_pkeep.parent.identifiant_unique == c3pkeep.identifiant_unique
        c3child1_pdelete = RevisionActeur.objects.get(pk="c3child1_pdelete")
        assert c3child1_pdelete.parent.identifiant_unique == c3pkeep.identifiant_unique
        c3orphan = RevisionActeur.objects.get(pk="c3orphan")
        assert c3orphan.parent.identifiant_unique == c3pkeep.identifiant_unique

        # The all important test of unkept parent which
        # must be deleted
        assert not RevisionActeur.objects.filter(pk="c3pdelete").exists()
