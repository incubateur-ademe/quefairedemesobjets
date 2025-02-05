from datetime import datetime

import pytest

from dags.cluster.tasks.business_logic import cluster_acteurs_suggestions_to_db
from dags_unit_tests.cluster.tasks.business_logic.test_data import df_get
from data.models import Suggestion, SuggestionCohorte


@pytest.mark.django_db()
class TestClusterActeursSuggestionsToDb:
    """TODO: rajouter des tests sur les attentes
    des données créées en base
    """

    @pytest.fixture
    def df(self):
        return df_get()

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
        assert cohorts.count() == 1

    def test_one_suggestion_per_cluster(self, df, suggestions):
        assert suggestions.count() == df["cluster_id"].nunique()

    def test_each_suggestion_has_one_change_per_acteur(self, df, suggestions):
        # On parcours toutes les suggestions, on identifie son cluster,
        # on récupère le cluster correspondant de la df, et on vérifier
        # que la suggestion et la df ont les mêmes acteurs
        cluster_ids_found = set()
        for s in suggestions:
            change_list = s.suggestion
            cluster_id = change_list[0]["cluster_id"]
            cluster_ids_found.add(cluster_id)
            cluster = df[df["cluster_id"] == cluster_id]
            assert sorted(cluster["id"].tolist()) == sorted(
                [x["id"] for x in change_list]
            )

        # Et on doit avoir trouvé tous les clusters de la df
        cluster_ids_missing = set(df["cluster_id"].unique()) - cluster_ids_found
        assert not cluster_ids_missing
