from datetime import datetime

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_suggestions_to_db import (
    cluster_acteurs_suggestions_to_db,
)

from data.models import Suggestion, SuggestionCohorte
from data.models.change import (
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
    COL_CHANGE_TYPE,
    COL_ENTITY_TYPE,
)

ID = "identifiant_unique"

COLS = [
    COL_CHANGE_ORDER,
    COL_ENTITY_TYPE,
    "identifiant_unique",
    COL_CHANGE_TYPE,
    COL_CHANGE_REASON,
]


@pytest.mark.django_db()
class TestClusterActeursSuggestionsToDb:
    """TODO: rajouter des tests sur les attentes
    des données créées en base
    """

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            [
                # c1 = 2 changements
                [1, "acteur", "a1", "create", "r_create", "c1", 0],
                [2, "acteur", "a2", "point", "r_point", "c1", 0],
                # c2 = 3 changements
                [1, "acteur", "a3", "create", "r_create", "c2", 0],
                [2, "acteur", "a4", "point", "r_point", "c2", 0],
                [3, "acteur", "a5", "delete", "r_delete", "c2", 1],
                # Gap intentionnel où c3 n'est pas présent
                # c4 = 5 changements
                [1, "acteur", "a6", "create", "r_create", "c4", 0],
                [2, "acteur", "a7", "point", "r_point", "c4", 0],
                [2, "acteur", "a8", "point", "r_point", "c4", 0],
                [3, "acteur", "a9", "delete", "r_delete", "c4", 1],
                [3, "acteur", "a10", "delete", "r_delete", "c4", 1],
                # On ajoute nombre_enfants requis par df_metadata_get
            ],
            columns=COLS + ["cluster_id", "nombre_enfants"],
        )

    @pytest.fixture
    def now(self):
        return datetime.now().strftime("%Y%m%d%H%M%S")

    @pytest.fixture
    def id_action(self, now):
        return f"test action {now}"

    @pytest.fixture
    def id_execution(self, now):
        return f"test execution {now}"

    @pytest.fixture(autouse=True)
    def suggestions_to_db(self, df, id_action, id_execution):
        cluster_acteurs_suggestions_to_db(
            df_clusters=df,
            identifiant_action=id_action,
            identifiant_execution=id_execution,
        )

    @pytest.fixture
    def cohorts(self, id_action, id_execution):
        return SuggestionCohorte.objects.filter(
            identifiant_action=id_action, identifiant_execution=id_execution
        )

    @pytest.fixture
    def suggestions(self, cohorts):
        return Suggestion.objects.filter(suggestion_cohorte=cohorts.first())

    def test_one_cohort_created_per_run(self, cohorts):
        # 1 cohorte par run
        assert cohorts.count() == 1

    def test_one_suggestion_per_cluster(self, df, suggestions):
        # Autant de suggestions que de clusters
        assert suggestions.count() == df["cluster_id"].nunique()

    def test_each_suggestion_has_one_change_per_acteur(self, df, suggestions):
        # On parcours toutes les suggestions, on identifie son cluster,
        # on récupère le cluster correspondant de la df, et on vérifier
        # que la suggestion et la df ont les mêmes acteurs
        cluster_ids_found = set()
        for s in suggestions:
            cluster_id = s.suggestion["cluster_id"]
            changes = s.suggestion["changes"]
            cluster_ids_found.add(cluster_id)
            cluster = df[df["cluster_id"] == cluster_id]
            assert len(cluster) == len(changes)
            assert sorted(cluster["identifiant_unique"].tolist()) == sorted(
                [x["identifiant_unique"] for x in changes]
            )

        # Et on doit avoir trouvé tous les clusters de la df
        cluster_ids_missing = set(df["cluster_id"].unique()) - cluster_ids_found
        assert not cluster_ids_missing
